"""Step 0 tests — causal pivot detection.

The load-bearing test here is truncation invariance. Pivot detection is
inherently non-causal, and the leak sits upstream of any window-level guard, so
a window test cannot catch it. Only "does appending future bars change a past
value" can.
"""
import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

from ml_patterns.pivots.causal_pivots import (
    confirmed_pivots, pivot_state, _raw_pivots, PIVOT_HIGH, PIVOT_LOW,
)


def _ohlcv(closes, highs=None, lows=None):
    closes = np.asarray(closes, dtype=float)
    highs = closes if highs is None else np.asarray(highs, dtype=float)
    lows = closes if lows is None else np.asarray(lows, dtype=float)
    idx = pd.bdate_range("2024-01-01", periods=len(closes))
    return pd.DataFrame({"open": closes, "high": highs, "low": lows,
                         "close": closes, "volume": np.ones(len(closes))},
                        index=idx)


def test_raw_pivot_finds_the_obvious_peak():
    # single clean peak at position 3
    df = _ohlcv([1, 2, 3, 9, 3, 2, 1])
    piv = _raw_pivots(df["high"].to_numpy(), df["low"].to_numpy(), k=2)
    highs = [(p, kind) for p, kind, _ in piv if kind == PIVOT_HIGH]
    assert highs == [(3, PIVOT_HIGH)]


def test_raw_pivot_ignores_plateau():
    """A flat top is ambiguous; strictness makes it produce NO pivot rather than
    an arbitrarily chosen one."""
    df = _ohlcv([1, 2, 9, 9, 2, 1, 0])
    piv = _raw_pivots(df["high"].to_numpy(), df["low"].to_numpy(), k=2)
    assert [(p, k) for p, k, _ in piv if k == PIVOT_HIGH] == []


def test_confirmation_lag_is_exactly_k():
    df = _ohlcv([1, 2, 3, 9, 3, 2, 1, 0, 1, 2])
    piv = confirmed_pivots(df, k=2)
    row = piv[piv["kind"] == PIVOT_HIGH].iloc[0]
    assert row["pos"] == 3
    assert row["confirm_pos"] == 5                 # pos + k
    assert row["confirm_time"] == df.index[5]


def test_unconfirmed_tail_pivot_is_dropped_not_reported_early():
    """A candidate peak too close to the right edge is genuinely unknowable.
    Reporting it would be exactly the leak this module prevents."""
    # peak at position 7 of an 9-bar frame, k=2 -> confirm_pos 9 == len -> dropped
    df = _ohlcv([1, 2, 1, 2, 1, 2, 3, 9, 3])
    assert len(df) == 9
    piv = confirmed_pivots(df, k=2)
    assert (piv["pos"] == 7).sum() == 0


def test_pivot_state_is_nan_until_confirmation_bar():
    df = _ohlcv([1, 2, 3, 9, 3, 2, 1, 0, 1, 2])
    st = pivot_state(df, k=2)
    # peak is at bar 3, confirmed at bar 5 -> invisible at 3 and 4
    assert np.isnan(st["last_high_price"].iloc[3])
    assert np.isnan(st["last_high_price"].iloc[4])
    assert st["last_high_price"].iloc[5] == pytest.approx(9.0)
    # age counts from the pivot bar itself, not its confirmation bar
    assert st["last_high_age"].iloc[5] == pytest.approx(2.0)
    assert st["last_high_age"].iloc[6] == pytest.approx(3.0)


def test_pivot_state_truncation_invariance():
    """THE load-bearing test. Values at bar T must not change when later bars
    are appended. A non-causal detector (e.g. raw argrelextrema over the full
    series) fails this immediately."""
    rng = np.random.default_rng(7)
    closes = 100 * np.cumprod(1 + rng.normal(0, 0.02, 200))
    df = _ohlcv(closes, highs=closes * 1.01, lows=closes * 0.99)
    full = pivot_state(df, k=3)
    for cut in (60, 100, 137, 199):
        partial = pivot_state(df.iloc[:cut], k=3)
        pd.testing.assert_frame_equal(full.iloc[:cut], partial)


def test_pivot_state_truncation_invariance_holds_for_several_k():
    rng = np.random.default_rng(11)
    closes = 50 * np.cumprod(1 + rng.normal(0, 0.015, 150))
    df = _ohlcv(closes, highs=closes * 1.02, lows=closes * 0.98)
    for k in (1, 2, 5, 10):
        full = pivot_state(df, k=k)
        partial = pivot_state(df.iloc[:120], k=k)
        pd.testing.assert_frame_equal(full.iloc[:120], partial)


def test_naive_centred_rolling_would_fail_this_guard():
    """Positive control: the guard has teeth. A naive centred rolling max is the
    standard wrong implementation; assert it genuinely breaks truncation
    invariance, so passing the test above means something."""
    rng = np.random.default_rng(3)
    closes = 100 * np.cumprod(1 + rng.normal(0, 0.02, 120))
    df = _ohlcv(closes, highs=closes * 1.01, lows=closes * 0.99)

    def naive_state(d, k):                      # centred window, no lag
        return (d["high"].rolling(2 * k + 1, center=True).max()
                .rename("naive").to_frame())

    full = naive_state(df, 3)
    partial = naive_state(df.iloc[:100], 3)
    with pytest.raises(AssertionError):
        pd.testing.assert_frame_equal(full.iloc[:100], partial)


def test_lows_are_detected_symmetrically():
    df = _ohlcv([9, 8, 7, 1, 7, 8, 9, 10, 11])
    piv = confirmed_pivots(df, k=2)
    lows = piv[piv["kind"] == PIVOT_LOW]
    assert len(lows) == 1 and lows.iloc[0]["pos"] == 3
    st = pivot_state(df, k=2)
    assert st["last_low_price"].iloc[5] == pytest.approx(1.0)


def test_empty_and_short_frames_do_not_crash():
    assert len(confirmed_pivots(_ohlcv([]), k=2)) == 0
    assert len(confirmed_pivots(_ohlcv([1, 2, 3]), k=5)) == 0
    st = pivot_state(_ohlcv([1, 2, 3]), k=5)
    assert len(st) == 3 and st["last_high_price"].isna().all()
