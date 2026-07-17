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
    target_index = pd.DatetimeIndex(target_index)
    if foreign is None or len(foreign) == 0:
        return pd.DataFrame(index=target_index, columns=cols, dtype=float)
    left = pd.DataFrame({"_t": target_index}).sort_values("_t")
    right = foreign.sort_index().reset_index()
    right.columns = ["_f"] + cols
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
    legs, causal-z-scored. Same underlying so the fair ratio is 1 (no beta fit)."""
    adr_close = _asof_align(target_df.index, adr_df[["close"]], strict_before=True)["close"]
    fx = _asof_align(target_df.index, fx_df[["close"]], strict_before=True)["close"]
    adr_krw = adr_close * fx * adr_ratio
    premium = adr_krw / target_df["close"] - 1.0
    return _causal_zscore(premium, window).rename("xmkt_adr_premium")


def adr_premium_snapshot(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                         fx_df: pd.DataFrame, adr_ratio: float = 1.0,
                         band: float = 0.03) -> dict:
    """Live descriptive premium from the latest available print of each venue."""
    adr, fx, local = _last_finite(adr_df), _last_finite(fx_df), _last_finite(target_df)
    if not np.isfinite([adr, fx, local]).all() or local == 0:
        return {"available": False, "reason": "missing ADR / FX / local price"}
    adr_krw = adr * fx * adr_ratio
    premium = adr_krw / local - 1.0
    zone = "rich" if premium > band else "cheap" if premium < -band else "within_band"
    return {"available": True, "adr_price": round(adr, 4), "fx": round(fx, 4),
            "adr_ratio": adr_ratio, "adr_in_krw": round(adr_krw, 2),
            "local_price": round(local, 2), "premium_pct": round(100 * premium, 2),
            "band_pct": round(100 * band, 2), "zone": zone}
