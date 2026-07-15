"""Decorrelated personality-sets. Each set is a 4-slot composite of z-scored,
sign-aligned indicators; personalities differ by which member fills each slot
(round-robin, distinct) and, for Contrarian, an inverted sign. Member signs are
fit on the TRAIN slice only, so the later holdout IC is honest. A seeded-random
'Null' set rides along as a leakage tripwire."""
from itertools import combinations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
from pandasta_registry import build_candidates, compute_candidate
import stats as st

SLOTS = ("trend", "momentum", "volatility", "volume")
PERSONALITIES = ("Fast", "Slow", "Contrarian")
NULL_NAME = "Null"

# Causal rolling z-score (inlined from the former pandasta_set_search reuse so
# this package is self-contained). 252-bar window, 126-bar warm-up.
_Z_WINDOW, _Z_MIN = 252, 126


def causal_zscore(x: pd.Series) -> pd.Series:
    mu = x.rolling(_Z_WINDOW, min_periods=_Z_MIN).mean()
    sd = x.rolling(_Z_WINDOW, min_periods=_Z_MIN).std()
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (x - mu) / sd
    return z.replace([np.inf, -np.inf], np.nan)


def _train_slice(n: int) -> int:
    return max(config.REGIME_MA_LEN + config.HORIZON, int(n * config.TRAIN_FRAC))


def _member_sign(z: pd.Series, fwd: np.ndarray, split: int) -> float:
    """+/-1 from the member's IC on the TRAIN slice only (0/NaN -> +1)."""
    ic, _, _, _ = st.spearman_ic_hac(z.to_numpy("float64")[:split], fwd[:split],
                                     lag=config.HORIZON)
    return -1.0 if (np.isfinite(ic) and ic < 0) else 1.0


def _candidates_by_slot(df: pd.DataFrame) -> dict[str, list[pd.Series]]:
    by_slot: dict[str, list[pd.Series]] = {s: [] for s in SLOTS}
    for cand in build_candidates():
        if cand.slot not in by_slot:
            continue
        try:
            raw = compute_candidate(df, cand)
        except Exception:
            continue
        z = causal_zscore(raw)
        if z.notna().sum() > config.REGIME_MA_LEN:
            by_slot[cand.slot].append(z.rename(cand.name))
    return by_slot


def build_set_signals(df: pd.DataFrame, mode: str = "log") -> dict[str, pd.Series]:
    n = len(df)
    split = _train_slice(n)
    fwd = st.forward_returns(df["close"].to_numpy("float64"), config.HORIZON, mode)
    by_slot = _candidates_by_slot(df)

    signals: dict[str, pd.Series] = {}
    for p_idx, pname in enumerate(PERSONALITIES):
        members = []
        for slot in SLOTS:
            pool = by_slot[slot]
            if not pool:
                continue
            z = pool[p_idx % len(pool)]
            members.append(_member_sign(z, fwd, split) * z)
        if not members:
            signals[pname] = pd.Series(np.nan, index=df.index, name=pname)
            continue
        comp = pd.concat(members, axis=1).mean(axis=1)
        if pname == "Contrarian":
            comp = -comp
        signals[pname] = comp.rename(pname)

    # Null tripwire: seeded random signal through the same sign machinery.
    rng = np.random.default_rng(config.NULL_SEED)
    null_z = causal_zscore(pd.Series(rng.standard_normal(n), index=df.index))
    signals[NULL_NAME] = (_member_sign(null_z, fwd, split) * null_z).rename(NULL_NAME)
    return signals


def _pairwise_report(cols: dict[str, pd.Series], threshold: float) -> dict:
    names = list(cols)
    mat = pd.concat([cols[n] for n in names], axis=1).dropna()
    pairs, max_abs = {}, 0.0
    for a, b in combinations(names, 2):
        c = float(mat[a].corr(mat[b])) if len(mat) > 2 else 0.0
        c = 0.0 if not np.isfinite(c) else c
        pairs[f"{a}~{b}"] = c          # str key so the report is JSON-serializable
        max_abs = max(max_abs, abs(c))
    return {"max_abs_corr": max_abs, "pairs": pairs, "ok": max_abs <= threshold}


def check_decorrelation(signals: dict[str, pd.Series], threshold: float) -> dict:
    return _pairwise_report(signals, threshold)


def check_error_decorrelation(signals: dict[str, pd.Series], df: pd.DataFrame,
                              mode: str, window: int, threshold: float) -> dict:
    """Correlated errors, not correlated signals: correlate each set's rolling-IC series."""
    fwd = st.forward_returns(df["close"].to_numpy("float64"), config.HORIZON, mode)
    ic_series = {}
    for name, s in signals.items():
        roll = st.rolling_spearman(s.to_numpy("float64"), fwd, window)
        ic_series[name] = pd.Series(roll, index=df.index, name=name)
    return _pairwise_report(ic_series, threshold)
