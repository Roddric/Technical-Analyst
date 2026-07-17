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


def test_adr_overnight_signal_values_are_causal():
    # ADR returns: [nan, +0.10, +0.10, 0.0]. Strict-before alignment to targets
    # 01-03/01-04/01-05 -> [0.10, 0.10, 0.0]; causal z(window=2) -> [nan, nan, -0.7071].
    # A leaky (same-date) alignment would give [0.10, 0.0, 0.0] -> z [nan, -0.7071, nan],
    # so asserting the finite value lands at index 2 (not index 1) pins the causal guard
    # to the FUNCTION's own output.
    adr = _frame(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"], [100, 110, 121, 121])
    target = _frame(["2021-01-03", "2021-01-04", "2021-01-05"], [1, 1, 1])
    sig = cross_market.adr_overnight_signal(target, adr, window=2)
    assert sig.name == "xmkt_adr_overnight"
    assert list(sig.index) == list(target.index)
    assert np.isnan(sig.iloc[0]) and np.isnan(sig.iloc[1])
    assert sig.iloc[2] == pytest.approx((0.0 - 0.05) / np.std([0.10, 0.0], ddof=1))


def test_adr_premium_snapshot_matches_hand_calc():
    # 152.31 * 1480 = 225418.8 ; / 228500 - 1 = -1.349% -> -1.35
    target = _frame(["2026-07-15", "2026-07-16"], [228500, 228500])
    adr = _frame(["2026-07-14", "2026-07-15"], [150.0, 152.31])
    fx = _frame(["2026-07-14", "2026-07-15"], [1480.0, 1480.0])
    snap = cross_market.adr_premium_snapshot(target, adr, fx, adr_ratio=1.0)
    assert snap["available"] is True
    assert snap["premium_pct"] == pytest.approx(-1.35, abs=0.01)
    assert snap["zone"] == "within_band"


def test_adr_premium_snapshot_zone_bands():
    target = _frame(["2026-01-01"], [100.0])
    adr_rich = _frame(["2026-01-01"], [110.0])          # +10% -> rich
    fx = _frame(["2026-01-01"], [1.0])
    assert cross_market.adr_premium_snapshot(target, adr_rich, fx, 1.0)["zone"] == "rich"
    adr_cheap = _frame(["2026-01-01"], [90.0])           # -10% -> cheap
    assert cross_market.adr_premium_snapshot(target, adr_cheap, fx, 1.0)["zone"] == "cheap"


def test_adr_premium_snapshot_missing_data_unavailable():
    target = _frame(["2026-01-01"], [100.0])
    empty = _frame([], [])
    snap = cross_market.adr_premium_snapshot(target, empty, empty, 1.0)
    assert snap["available"] is False


def test_adr_premium_signal_is_series_aligned_to_target():
    n = 80
    dates = pd.bdate_range("2021-01-01", periods=n)
    target = _frame(dates, np.linspace(200000, 230000, n))
    adr = _frame(dates, np.linspace(140, 155, n))
    fx = _frame(dates, np.full(n, 1480.0))
    sig = cross_market.adr_premium_signal(target, adr, fx, adr_ratio=1.0, window=20)
    assert sig.name == "xmkt_adr_premium"
    assert list(sig.index) == list(target.index)
    assert np.isfinite(sig.iloc[-1])           # enough history -> finite tail


def _long_legs(n=300):
    dates = pd.bdate_range("2020-01-01", periods=n)
    target = _frame(dates, np.linspace(200000, 230000, n))
    adr = _frame(dates, np.linspace(140, 155, n))
    fx = _frame(dates, np.full(n, 1480.0))
    return target, adr, fx


def test_build_signals_returns_both_with_fake_loader():
    target, adr, fx = _long_legs()
    loader = lambda t: {"US.SKHY": adr, "KRW=X": fx}.get(t)
    sigs = cross_market.build_signals(target, "000660.KS", loader=loader)
    assert set(sigs) == {"xmkt_adr_overnight", "xmkt_adr_premium"}
    assert all(len(s) == len(target) for s in sigs.values())


def test_build_signals_unconfigured_asset_is_empty():
    target, _, _ = _long_legs()
    assert cross_market.build_signals(target, "AAPL", loader=lambda t: None) == {}


def test_build_signals_missing_leg_is_empty():
    target, _, _ = _long_legs()
    assert cross_market.build_signals(target, "000660.KS", loader=lambda t: None) == {}


def test_build_signals_short_history_is_empty():
    target, adr, fx = _long_legs(n=50)          # < XMKT_MIN_HISTORY
    loader = lambda t: {"US.SKHY": adr, "KRW=X": fx}.get(t)
    assert cross_market.build_signals(target, "000660.KS", loader=loader) == {}
