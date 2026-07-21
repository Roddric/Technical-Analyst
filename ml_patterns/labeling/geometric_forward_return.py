"""Step 1 — forward-return labelling for the geometric_forward_return signal.

The causality question INVERTS here. A feature at bar t may only use information
available at t. A label at bar t is by definition about the future — it is the
realised return over (t, t+h]. That is not a leak; it is the target.

The leak appears one level up, in WHEN a label may be used:

  * A label for bar t is not knowable until bar t+h.
  * Training on data "as of" time T may therefore only use labels for bars
    t <= T-h. Using label t = T means training on an outcome that has not
    happened yet.
  * Labels for nearby bars OVERLAP: labels at t and t+1 share h-1 days of
    future. A train/test split that merely cuts at a point leaks across the
    boundary through that shared window, which is what purging removes.

This module therefore never returns a bare label column. Every label carries the
bar at which it becomes known, and the train-mask helper is the only sanctioned
way to select training rows.

Naming: this is `geometric_forward_return`, not "pattern recognition". It reads
confirmed geometry (already k bars stale by construction — see pivots/) and asks
whether forward returns follow. It does not classify head-and-shoulders.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import stats as st


def forward_return_labels(df: pd.DataFrame, horizon: int = config.HORIZON,
                          mode: str = "log") -> pd.DataFrame:
    """Target for the signal, with its knowability made explicit.

    Columns:
        fwd_return   realised return over (t, t+h]; last h bars are NaN
        direction    sign of fwd_return as +1 / -1 / 0 (NaN where fwd is NaN)
        known_at_pos integer bar position at which this label becomes knowable
                     (t + horizon); NaN when that falls outside the frame
        known_at     the corresponding timestamp, or NaT

    Delegates the return construction to vendor/stats.py and re-asserts its
    structural lookahead guard, so this module cannot drift from the engine the
    rest of the system validates against.
    """
    cols = ["fwd_return", "direction", "known_at_pos", "known_at"]
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=cols, index=df.index if df is not None else pd.Index([]))

    close = df["close"].to_numpy("float64")
    fwd = st.forward_returns(close, horizon, mode)
    if horizon > 0 and horizon < len(close):
        st.assert_no_lookahead(fwd, horizon)      # structural guard, not decoration

    n = len(df)
    pos = np.arange(n)
    known_pos = pos + horizon
    inside = known_pos < n

    direction = np.where(np.isnan(fwd), np.nan, np.sign(fwd))
    out = pd.DataFrame({
        "fwd_return": fwd,
        "direction": direction,
        "known_at_pos": np.where(inside, known_pos, np.nan),
    }, index=df.index)
    out["known_at"] = pd.Series(
        [df.index[p] if ok else pd.NaT for p, ok in zip(known_pos, inside)],
        index=df.index)
    return out[cols]


def trainable_mask(labels: pd.DataFrame, asof_pos: int, horizon: int = config.HORIZON,
                   embargo: int = 0) -> np.ndarray:
    """Rows whose label is genuinely known by bar `asof_pos`, with embargo.

    A label at t is known at t+h, so training as of T admits t <= T-h. The
    embargo drops a further `embargo` bars immediately before that boundary:
    their forward windows still overlap the unseen period, and that overlap is
    the leak a plain cut leaves behind.

    Returns a boolean mask over the label rows.
    """
    n = len(labels)
    if n == 0:
        return np.zeros(0, dtype=bool)
    pos = np.arange(n)
    cutoff = asof_pos - horizon - max(0, embargo)
    return (pos <= cutoff) & labels["fwd_return"].notna().to_numpy()


def purge_overlapping(labels: pd.DataFrame, test_start_pos: int, test_end_pos: int,
                      horizon: int = config.HORIZON,
                      embargo: int = 0) -> np.ndarray:
    """Training rows for a test block spanning [test_start_pos, test_end_pos].

    Drops (a) the test block itself and (b) every training row whose forward
    window reaches into it — rows in [test_start - h, test_start) — plus an
    embargo after the block, where serial correlation still links the two.

    This is the minimal purge/embargo this signal needs. It is deliberately not
    a general CPCV framework: none exists in either repo, and building one is
    out of scope for v1.
    """
    n = len(labels)
    if n == 0:
        return np.zeros(0, dtype=bool)
    pos = np.arange(n)
    before = pos < (test_start_pos - horizon)
    after = pos > (test_end_pos + max(0, embargo))
    return (before | after) & labels["fwd_return"].notna().to_numpy()
