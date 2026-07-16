"""Structural price levels — swing-pivot support/resistance and dominant-swing
Fibonacci retracement/extension levels.

DESCRIPTIVE ONLY (Layer-1 facts). Consumed by OpenClaw via
indicators.py::compute_indicators. The mechanical council (selection/arbiter/
risk) must never import this module."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import pandas_ta  # noqa: F401  registers the .ta accessor

SWING_K = 3
LOOKBACK = 250
CLUSTER_ATR = 0.5
FALLBACK_CLUSTER_PCT = 0.0075
SR_MAX_LEVELS = 3
FIB_RETR = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXT = (1.272, 1.618)


def _atr(df: pd.DataFrame) -> float:
    a = df.ta.atr(length=14)
    if a is None or len(a) == 0:
        return float("nan")
    v = a.iloc[-1]
    return float(v) if np.isfinite(v) else float("nan")


def _last_close(df: pd.DataFrame) -> float:
    c = df["close"].dropna()
    return float(c.iloc[-1]) if len(c) else float("nan")


def _swing_points(df: pd.DataFrame, k: int = SWING_K,
                  lookback: int = LOOKBACK) -> list[tuple[pd.Timestamp, float, str]]:
    """Fractal pivots over the last min(lookback, len(df)) bars.

    Swing high: high[t] >= max(left k) and high[t] > max(right k)   (left-loose,
    right-strict). Swing low is the mirror. A pivot at t is only emitted once its
    k forward bars exist, so the trailing k bars are never pivots (no look-ahead).
    """
    win = df.tail(min(lookback, len(df)))
    highs = win["high"].to_numpy(dtype=float)
    lows = win["low"].to_numpy(dtype=float)
    idx = win.index
    out: list[tuple[pd.Timestamp, float, str]] = []
    for t in range(k, len(win) - k):
        h, lo = highs[t], lows[t]
        if np.isfinite(h) and h >= highs[t - k:t].max() and h > highs[t + 1:t + k + 1].max():
            out.append((idx[t], float(h), "high"))
        if np.isfinite(lo) and lo <= lows[t - k:t].min() and lo < lows[t + 1:t + k + 1].min():
            out.append((idx[t], float(lo), "low"))
    out.sort(key=lambda p: p[0])
    return out
