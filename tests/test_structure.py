import json
import math

import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

import structure


def _frame(highs, lows=None, closes=None, start="2021-01-01"):
    """Flat-OHLC-friendly builder. Defaults low=close=high so extrema are clean."""
    n = len(highs)
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows if lows is not None else highs, dtype=float)
    closes = np.asarray(closes if closes is not None else highs, dtype=float)
    idx = pd.bdate_range(start, periods=n)
    return pd.DataFrame(
        {"open": closes, "high": highs, "low": lows, "close": closes,
         "volume": np.full(n, 1000.0)},
        index=idx,
    )


def _zigzag(anchors, seg=6):
    """Piecewise-linear path through `anchors`; each interior anchor is a clean
    k=3 pivot. Anchor i sits at position i*seg. Flat OHLC (high=low=close)."""
    vals = []
    for a, b in zip(anchors[:-1], anchors[1:]):
        seg_vals = np.linspace(a, b, seg + 1)
        vals.extend(seg_vals[:-1])          # drop shared endpoint
    vals.append(anchors[-1])
    return _frame(vals)


def test_swing_points_single_peak_and_trough():
    df = _frame([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])   # apex at index 5
    piv = structure._swing_points(df, k=3)
    highs = [(d, p) for d, p, kind in piv if kind == "high"]
    assert len(highs) == 1
    assert highs[0][0] == df.index[5]
    assert highs[0][1] == 6.0


def test_swing_points_causal_confirmation():
    df = _frame([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])   # apex t=5, k=3
    t, k = 5, 3
    before = structure._swing_points(df.iloc[: t + k], k=k)      # df[:8]
    after = structure._swing_points(df.iloc[: t + k + 1], k=k)   # df[:9]
    assert all(d != df.index[t] for d, _, _ in before)          # not yet confirmed
    assert any(d == df.index[t] for d, _, _ in after)           # confirmed at t+k


def test_swing_points_trailing_k_never_pivots():
    df = _frame([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
    k = 3
    piv = structure._swing_points(df, k=k)
    trailing = set(df.index[-k:])
    assert all(d not in trailing for d, _, _ in piv)


def test_swing_high_flat_top_picks_rightmost():
    # plateau at positions 3,4 (value 5); constant lows -> no low pivots
    df = _frame(highs=[1, 2, 3, 5, 5, 4, 3, 2, 1], lows=[0.5] * 9)
    piv = structure._swing_points(df, k=3)
    highs = [d for d, _, kind in piv if kind == "high"]
    assert len(highs) == 1
    assert highs[0] == df.index[4]      # rightmost bar of the plateau


def test_swing_low_flat_bottom_picks_rightmost():
    # trough plateau at positions 3,4 (value 5); constant highs -> no high pivots
    df = _frame(highs=[9] * 9, lows=[9, 8, 7, 5, 5, 6, 7, 8, 9])
    piv = structure._swing_points(df, k=3)
    lows = [d for d, _, kind in piv if kind == "low"]
    assert len(lows) == 1
    assert lows[0] == df.index[4]
