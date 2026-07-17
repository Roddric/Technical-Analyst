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
