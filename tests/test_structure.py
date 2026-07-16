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


def test_sr_clusters_repeated_touches_into_one_zone():
    # two swing highs at ~150 (positions 6 and 18), lows near 100, current ~120
    df = _zigzag([120, 100, 150, 100, 150, 100, 120], seg=6)
    out = structure.support_resistance(df, cluster_atr=5.0)
    assert out["available"] is not False
    res = out["resistances"]
    # the two 150 highs collapse into a single zone with touches >= 2
    assert any(abs(z["price"] - 150) < 2 and z["touches"] >= 2 for z in res)


def test_sr_distinct_prices_stay_separate():
    df = _zigzag([120, 100, 150, 100, 180, 100, 120], seg=6)
    out = structure.support_resistance(df, cluster_atr=0.1)
    prices = sorted(z["price"] for z in out["resistances"])
    assert any(abs(p - 150) < 2 for p in prices)
    assert any(abs(p - 180) < 2 for p in prices)


def test_sr_splits_by_current_price_and_caps_levels():
    df = _zigzag([120, 90, 160, 95, 170, 100, 130], seg=6)
    out = structure.support_resistance(df, cluster_atr=0.1, max_levels=1)
    price = float(df["close"].iloc[-1])
    assert len(out["supports"]) <= 1 and len(out["resistances"]) <= 1
    assert all(z["price"] < price for z in out["supports"])
    assert all(z["price"] > price for z in out["resistances"])


def test_sr_atr_fallback_when_atr_nan(monkeypatch):
    df = _zigzag([120, 100, 150, 100, 150, 100, 120], seg=6)
    monkeypatch.setattr(structure, "_atr", lambda d: float("nan"))
    out = structure.support_resistance(df)
    assert "0.75%" in out["method"] or "ATR unavailable" in out["method"]


def test_sr_unavailable_when_no_pivots():
    df = _frame([100.0] * 300)          # perfectly flat -> no swings
    out = structure.support_resistance(df)
    assert out == {"available": False, "reason": out["reason"]}
    assert out["available"] is False
