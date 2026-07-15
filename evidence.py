"""Evidence weights via a unified power-gate + shrink on the HAC t-stat,
with FDR control applied across the (asset x set) grid at the universe level."""
import numpy as np
import pandas as pd
from scipy.stats import norm

import config
config.ensure_reuse_on_path()
import stats as st


def _holdout_split(n: int) -> int:
    return max(config.REGIME_MA_LEN + config.HORIZON, int(n * config.TRAIN_FRAC))


def set_ic_stats(signals: dict[str, pd.Series], df: pd.DataFrame,
                 mode: str = "log") -> dict[str, tuple[float, float, int]]:
    n = len(df)
    split = _holdout_split(n)
    fwd = st.forward_returns(df["close"].to_numpy("float64"), config.HORIZON, mode)
    out: dict[str, tuple[float, float, int]] = {}
    for name, s in signals.items():
        x = s.to_numpy("float64")[split:]
        y = fwd[split:]
        ic, t, _, nobs = st.spearman_ic_hac(x, y, lag=config.HORIZON)
        out[name] = (float(ic), float(t) if np.isfinite(t) else 0.0,
                     int(nobs) if np.isfinite(nobs) else 0)
    return out


def detectable_ic(ic: float, t: float) -> float:
    """Readable 1.96*SE significance floor (SE inferred from the HAC t-stat)."""
    if not np.isfinite(t) or t == 0 or not np.isfinite(ic):
        return float("inf")
    return 1.96 * abs(ic / t)


def weight_from_stat(ic: float, t: float, k: float = config.GATE_K) -> float:
    """Unified gate+shrink: max(0, ic*(1 - k/t)) for t>=k and ic>0, else 0."""
    if not np.isfinite(ic) or not np.isfinite(t) or ic <= 0 or t < k:
        return 0.0
    return ic * (1.0 - k / t)


def one_sided_p(t: float) -> float:
    if not np.isfinite(t):
        return 1.0
    return float(norm.sf(t))


def fdr_survivors(pvals: dict, q: float = config.FDR_Q) -> set:
    """Benjamini-Hochberg: return the set of keys that survive at level q."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    if m == 0:
        return set()
    cutoff_rank = 0
    for i, (_, p) in enumerate(items, start=1):
        if p <= (i / m) * q:
            cutoff_rank = i
    return {k for i, (k, _) in enumerate(items, start=1) if i <= cutoff_rank}


def compute_weights(signals: dict[str, pd.Series], df: pd.DataFrame,
                    mode: str = "log", allowed: set | None = None,
                    k: float = config.GATE_K) -> dict[str, float]:
    stats = set_ic_stats(signals, df, mode)
    raw: dict[str, float] = {}
    for name, (ic, t, _n) in stats.items():
        if allowed is not None and name not in allowed:
            continue
        raw[name] = weight_from_stat(ic, t, k)
    total = sum(raw.values())
    if total <= 0:
        return {}
    return {name: v / total for name, v in raw.items() if v > 0}
