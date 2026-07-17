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
                       window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Premium reversion: (ADR-in-KRW / local) - 1, on causally-aligned foreign
    legs, causal-z-scored. Same underlying, so no beta fit is needed (price beta
    = 1); the ADR-to-share count is handled by adr_ratio (e.g. 10 ADRs/share)."""
    adr_close = _asof_align(target_df.index, adr_df[["close"]], strict_before=True)["close"]
    fx = _asof_align(target_df.index, fx_df[["close"]], strict_before=True)["close"]
    adr_krw = adr_close * fx * adr_ratio
    premium = adr_krw / target_df["close"] - 1.0
    return _causal_zscore(premium, window).rename("xmkt_adr_premium")


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


def build_signals(target_df: pd.DataFrame, asset: str, loader=load_asset) -> dict:
    """Load the configured foreign legs and return the cross-market signal series
    for `asset`. Returns {} if unconfigured or data is missing/too short."""
    cfg = config.CROSS_MARKET_MAP.get(asset)
    if not cfg:
        return {}
    if target_df is None or target_df.empty:
        return {}
    adr_df, fx_df = loader(cfg["adr"]), loader(cfg["fx"])
    if adr_df is None or adr_df.empty or fx_df is None or fx_df.empty:
        return {}
    ratio = cfg.get("adr_ratio", 1.0)
    candidates = {
        "xmkt_adr_overnight": adr_overnight_signal(target_df, adr_df),
        "xmkt_adr_premium": adr_premium_signal(target_df, adr_df, fx_df, ratio),
    }
    return {name: s for name, s in candidates.items()
            if s.notna().sum() >= XMKT_MIN_HISTORY}
