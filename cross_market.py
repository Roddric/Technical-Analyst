"""Cross-market (cross-listing) signals for SK Hynix — Phase A.

Treats 000660.KS (Korea, the anchor) and US.SKHY (the US ADR, same underlying)
as one asset in two venues. Produces two causally-aligned mechanical signals
(overnight transmission, premium reversion) plus a live premium snapshot.

CAUSAL: every foreign leg is attached with an as-of BACKWARD merge; for the
Korea target the foreign date must be strictly before the target date, because a
US close dated D only prints ~06:00 KST on D+1 (after KRX closes on D)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
from pandasta_data import load_asset

XMKT_Z_WINDOW = config.XMKT_Z_WINDOW
XMKT_MIN_HISTORY = config.XMKT_MIN_HISTORY


def _asof_align(target_index: pd.DatetimeIndex, foreign: pd.DataFrame,
                strict_before: bool = True) -> pd.DataFrame:
    """Reindex `foreign` onto `target_index` by as-of backward merge.
    strict_before=True -> foreign date must be < target date (no same-date match)."""
    cols = list(foreign.columns)
    # Coerce to a single datetime64 resolution — real yfinance/CSV data mixes
    # [s]/[us]/[ns], and merge_asof requires the two merge keys to match exactly.
    target_index = pd.DatetimeIndex(target_index).astype("datetime64[ns]")
    if foreign is None or len(foreign) == 0:
        return pd.DataFrame(index=target_index, columns=cols, dtype=float)
    left = pd.DataFrame({"_t": target_index}).sort_values("_t")
    right = foreign.sort_index().reset_index()
    right.columns = ["_f"] + cols
    right["_f"] = pd.DatetimeIndex(right["_f"]).astype("datetime64[ns]")
    merged = pd.merge_asof(left, right, left_on="_t", right_on="_f",
                           direction="backward", allow_exact_matches=not strict_before)
    merged.index = pd.DatetimeIndex(merged["_t"])
    return merged[cols].reindex(target_index)


def _causal_zscore(s: pd.Series, window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Trailing-window z-score using only data up to each point; non-finite -> NaN."""
    mean = s.rolling(window).mean()
    std = s.rolling(window).std()
    z = (s - mean) / std
    return z.replace([np.inf, -np.inf], np.nan)


def adr_overnight_signal(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                         window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Transmission: the ADR's freshest daily return available before the Korea
    bar (as-of, strictly before), causal-z-scored. Sign/weight learned OOS."""
    adr_ret = adr_df["close"].pct_change().to_frame("adr_ret")
    aligned = _asof_align(target_df.index, adr_ret, strict_before=True)["adr_ret"]
    return _causal_zscore(aligned, window).rename("xmkt_adr_overnight")


def _last_finite(df: pd.DataFrame) -> float:
    if df is None or "close" not in df or len(df) == 0:
        return float("nan")
    c = df["close"].dropna()
    return float(c.iloc[-1]) if len(c) else float("nan")


def adr_premium_signal(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                       fx_df: pd.DataFrame, adr_ratio: float = 1.0,
                       window: int = XMKT_Z_WINDOW,
                       regime_start=None) -> pd.Series:
    """Premium reversion: (ADR-in-KRW / local) - 1, on causally-aligned foreign
    legs, causal-z-scored. Same underlying, so no beta fit is needed (price beta
    = 1); the ADR-to-share count is handled by adr_ratio (e.g. 10 ADRs/share).

    OPTIONALLY REGIME-GATED, per pair. Where two-way conversion opened partway
    through the sample, the earlier era is a one-way scarcity premium with a
    different mean, so bars before `regime_start` are DROPPED before z-scoring
    — not masked after it, which would still let scarcity-premium values sit in
    the trailing mean/std of a post-conversion bar.

    `regime_start=None` means NO SPLIT: the pair has had two-way conversion for
    the whole sample (the normal case for a mature ADR like TSM). The date is a
    property of the PAIR and lives in CROSS_MARKET_MAP — never a module-level
    default, which would silently apply one pair's regime date to every other."""
    adr_close = _asof_align(target_df.index, adr_df[["close"]], strict_before=True)["close"]
    fx = _asof_align(target_df.index, fx_df[["close"]], strict_before=True)["close"]
    adr_krw = adr_close * fx * adr_ratio
    premium = adr_krw / target_df["close"] - 1.0
    if regime_start is None:
        post = premium
    else:
        post = premium[pd.DatetimeIndex(premium.index) >= pd.Timestamp(regime_start)]
    z = _causal_zscore(post, window)
    return z.reindex(premium.index).rename("xmkt_adr_premium")


def adr_premium_snapshot(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                         fx_df: pd.DataFrame, adr_ratio: float = 1.0,
                         band: float = 0.03) -> dict:
    """Live descriptive premium from the latest available print of each venue.
    adr_ratio = ADRs per local share (scales the ADR price up to a full-share
    basis). Flags the pre/post two-way-conversion regime, because before
    conversion opens the premium is a scarcity premium, not a reverting spread."""
    adr, fx, local = _last_finite(adr_df), _last_finite(fx_df), _last_finite(target_df)
    if not np.isfinite([adr, fx, local]).all() or local == 0:
        return {"available": False, "reason": "missing ADR / FX / local price"}
    adr_krw = adr * fx * adr_ratio
    premium = adr_krw / local - 1.0
    zone = "rich" if premium > band else "cheap" if premium < -band else "within_band"
    conv = config.ADR_TWO_WAY_CONVERSION_DATE
    two_way = pd.Timestamp(target_df.index[-1]) >= pd.Timestamp(conv)
    regime = "two_way_active" if two_way else "scarcity_premium_one_way"
    regime_note = ("two-way ADR<->local conversion active; premium is a "
                   "mean-reverting arbitrage spread") if two_way else (
                   f"one-way conversion only until {conv}; premium is a scarcity "
                   "premium with no arbitrage force to parity — do NOT read it as a "
                   "mean-reverting spread yet")
    return {"available": True, "adr_price": round(adr, 4), "fx": round(fx, 4),
            "adr_ratio": adr_ratio, "adr_in_krw": round(adr_krw, 2),
            "local_price": round(local, 2), "premium_pct": round(100 * premium, 2),
            "band_pct": round(100 * band, 2), "zone": zone,
            "two_way_conversion_date": conv, "arbitrage_regime": regime,
            "regime_note": regime_note}


def _etf_anchor_return(etf_index: pd.DatetimeIndex, und_df: pd.DataFrame,
                       sub_df: pd.DataFrame | None) -> pd.Series:
    """Anchor return for each ETF bar: the underlying's SAME-DATE local return.

    Causal by market hours, not by lag: Korea closes 15:30 KST, HK closes 16:00
    HKT (= 15:00 KST +1h) — the Korea print is already public when HK marks. On
    Korea holidays there is no same-date bar, so fall back to the substitute's
    STRICTLY-BEFORE overnight return (which needs the causal as-of, having no
    such intraday guarantee)."""
    und_ret = und_df["close"].pct_change()
    und_ret.index = pd.DatetimeIndex(und_ret.index).astype("datetime64[ns]")
    idx = pd.DatetimeIndex(etf_index).astype("datetime64[ns]")
    anchor = und_ret.reindex(idx)                    # NaN where Korea did not trade
    if sub_df is not None and len(sub_df):
        sub_ret = sub_df["close"].pct_change().to_frame("r")
        anchor = anchor.fillna(_asof_align(idx, sub_ret, strict_before=True)["r"])
    return anchor


def etf_divergence_signal(etf_df: pd.DataFrame, und_df: pd.DataFrame,
                          sub_df: pd.DataFrame | None = None,
                          leverage: float = 2.0,
                          window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Leveraged-ETF divergence: how far the 2x ETF moved beyond 2x its
    underlying. Excess tends to revert as market-maker create/redeem arbitrage
    re-couples the ETF to the underlying, so this is a mean-reversion signal on
    the ETF's OWN forward return. Sign (expected negative — fade the
    over-reaction) and weight are learned OOS, never hardcoded."""
    etf_ret = etf_df["close"].pct_change()
    etf_ret.index = pd.DatetimeIndex(etf_ret.index).astype("datetime64[ns]")
    anchor = _etf_anchor_return(etf_df.index, und_df, sub_df)
    divergence = etf_ret - leverage * anchor
    return _causal_zscore(divergence, window).rename("xmkt_etf_divergence")


def etf_divergence_snapshot(etf_df: pd.DataFrame, und_df: pd.DataFrame,
                            sub_df: pd.DataFrame | None = None,
                            leverage: float = 2.0) -> dict:
    """Live descriptive read on the latest bar: is today's ETF move explained by
    the underlying, or is it over/under-reacting? Descriptive only — it carries
    no mechanical weight and is available long before the signal can emit."""
    if etf_df is None or "close" not in etf_df or len(etf_df) < 2:
        return {"available": False, "reason": "insufficient ETF history"}
    etf_ret = etf_df["close"].pct_change()
    anchor = _etf_anchor_return(etf_df.index, und_df, sub_df)
    e, a = float(etf_ret.iloc[-1]), float(anchor.iloc[-1])
    if not np.isfinite([e, a]).all():
        return {"available": False, "reason": "missing ETF or anchor return"}
    expected = leverage * a
    div = e - expected
    read = ("over-reacting vs %gx" % leverage) if div > 0 else (
           ("under-reacting vs %gx" % leverage) if div < 0 else "tracking %gx" % leverage)
    return {"available": True, "etf_return_pct": round(100 * e, 2),
            "anchor_return_pct": round(100 * a, 2), "leverage": leverage,
            "expected_return_pct": round(100 * expected, 2),
            "divergence_pct": round(100 * div, 2), "read": read,
            "note": "descriptive only; the mechanical signal is gated on "
                    "XMKT_MIN_HISTORY and may still be absent"}


def _adr_candidates(target_df, cfg, loader) -> dict:
    """Phase A shape: {"adr": ..., "fx": ...} — the ADR-vs-local pair."""
    adr_df, fx_df = loader(cfg["adr"]), loader(cfg["fx"])
    if adr_df is None or adr_df.empty or fx_df is None or fx_df.empty:
        return {}
    ratio = cfg.get("adr_ratio", 1.0)
    return {
        "xmkt_adr_overnight": adr_overnight_signal(target_df, adr_df),
        "xmkt_adr_premium": adr_premium_signal(target_df, adr_df, fx_df, ratio,
                                               regime_start=cfg.get("regime_start")),
    }


def _etf_candidates(target_df, cfg, loader) -> dict:
    """Phase B shape: {"underlying": ..., "leverage": ...} — the leveraged ETF.
    The substitute anchor is optional; without it, Korea holidays simply stay
    NaN and are excluded by the history gate rather than guessed at."""
    und_df = loader(cfg["underlying"])
    if und_df is None or und_df.empty:
        return {}
    sub = cfg.get("substitute")
    sub_df = loader(sub) if sub else None
    if sub_df is not None and sub_df.empty:
        sub_df = None
    lev = cfg.get("leverage", 2.0)
    return {"xmkt_etf_divergence": etf_divergence_signal(target_df, und_df, sub_df, lev)}


def build_signals(target_df: pd.DataFrame, asset: str, loader=load_asset) -> dict:
    """Load the configured foreign legs and return the cross-market signal series
    for `asset`. Dispatches on the SHAPE of the config entry (ADR-shaped vs
    ETF-shaped). Returns {} if unconfigured or data is missing/too short."""
    cfg = config.CROSS_MARKET_MAP.get(asset)
    if not cfg:
        return {}
    if target_df is None or target_df.empty:
        return {}
    if "adr" in cfg:
        candidates = _adr_candidates(target_df, cfg, loader)
    elif "underlying" in cfg:
        candidates = _etf_candidates(target_df, cfg, loader)
    else:
        return {}
    # xmkt_adr_premium counts POST-REGIME bars only (pre-conversion history was
    # dropped upstream), so it answers a different evidence question than the
    # plain history gate and carries its own threshold.
    min_bars = {"xmkt_adr_premium": config.XMKT_REGIME_MIN_BARS}
    return {name: s for name, s in candidates.items()
            if s.notna().sum() >= min_bars.get(name, XMKT_MIN_HISTORY)}
