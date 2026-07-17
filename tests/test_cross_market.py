import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

import cross_market


def _frame(dates, closes):
    """OHLCV frame with flat OHLC = close, on the given dates."""
    closes = np.asarray(closes, dtype=float)
    idx = pd.to_datetime(list(dates))
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes,
         "volume": np.ones(len(closes))},
        index=idx,
    )


def test_asof_strict_before_excludes_same_date():
    foreign = _frame(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
                     [10, 20, 30, 40])
    target = pd.to_datetime(["2021-01-02", "2021-01-03", "2021-01-04"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=True)
    # each target date maps to the PRIOR foreign date, never the same date
    assert list(aligned["close"].values) == [10.0, 20.0, 30.0]


def test_asof_allow_exact_uses_same_date():
    foreign = _frame(["2021-01-01", "2021-01-02", "2021-01-03"], [10, 20, 30])
    target = pd.to_datetime(["2021-01-02", "2021-01-03"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=False)
    assert list(aligned["close"].values) == [20.0, 30.0]


def test_asof_holiday_robust_and_no_future_leak():
    # foreign missing 2021-01-02; target 2021-01-03 falls back to 01-01
    foreign = _frame(["2021-01-01", "2021-01-04"], [10, 40])
    target = pd.to_datetime(["2021-01-03"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=True)
    assert aligned["close"].iloc[0] == 10.0            # last before D, not the future 40


def test_causal_zscore_is_causal_and_correct():
    s = pd.Series(np.arange(1, 21, dtype=float))
    full = cross_market._causal_zscore(s, window=5)
    partial = cross_market._causal_zscore(s.iloc[:10], window=5)
    assert full.iloc[9] == pytest.approx(partial.iloc[9])   # future bars don't move it
    # manual check at index 9: window = values 6..10, mean 8, std(ddof=1)=1.5811, z=(10-8)/1.5811
    assert full.iloc[9] == pytest.approx((10 - 8) / np.std([6, 7, 8, 9, 10], ddof=1))


def test_causal_zscore_flat_series_is_nan_not_inf():
    s = pd.Series([5.0] * 10)
    z = cross_market._causal_zscore(s, window=5)
    assert not np.isinf(z).any()
    assert z.iloc[-1] != z.iloc[-1] or np.isnan(z.iloc[-1])   # NaN, not inf
