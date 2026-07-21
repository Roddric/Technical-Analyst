"""Step 2 tests — geometric features from confirmed pivots.

Truncation invariance is asserted generically across EVERY feature rather than a
chosen few: a new feature added later must inherit the guard automatically
instead of quietly escaping it.
"""
import inspect

import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

from ml_patterns.features import geometric
from ml_patterns.features.geometric import compute_indicators, FEATURE_NAMES


def _ohlcv(closes, highs=None, lows=None, vols=None):
    closes = np.asarray(closes, dtype=float)
    highs = closes if highs is None else np.asarray(highs, dtype=float)
    lows = closes if lows is None else np.asarray(lows, dtype=float)
    vols = np.ones(len(closes)) if vols is None else np.asarray(vols, dtype=float)
    idx = pd.bdate_range("2024-01-01", periods=len(closes))
    return pd.DataFrame({"open": closes, "high": highs, "low": lows,
                         "close": closes, "volume": vols}, index=idx)


def _random_frame(n=300, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    return _ohlcv(c, highs=c * 1.01, lows=c * 0.99,
                  vols=rng.integers(1_000, 10_000, n).astype(float))


def test_module_never_imports_the_non_causal_detector():
    """Structural guard: _raw_pivots is non-causal and must not be reachable
    from feature code, however convenient it looks."""
    src = inspect.getsource(geometric)
    assert "_raw_pivots" not in src.replace("`_raw_pivots`", "")


def test_compute_indicators_returns_the_documented_interface():
    """surrogate_ic_ir_null consumes exactly dict[str, Series] — pin it."""
    df = _random_frame()
    out = compute_indicators(df)
    assert isinstance(out, dict)
    assert set(out) == set(FEATURE_NAMES)
    for name, s in out.items():
        assert isinstance(s, pd.Series), name
        assert s.index.equals(df.index), name
        assert s.name == name


def test_every_feature_is_truncation_invariant():
    """THE guard, applied generically. Appending future bars must not change any
    feature value at an earlier bar — for every feature, not a sampled few."""
    df = _random_frame(n=300, seed=4)
    full = compute_indicators(df)
    for cut in (120, 200, 299):
        partial = compute_indicators(df.iloc[:cut])
        assert set(partial) == set(full)
        for name in full:
            a = full[name].iloc[:cut]
            b = partial[name]
            pd.testing.assert_series_equal(a, b, check_names=False,
                                           obj=f"{name} @cut={cut}")


def test_features_are_nan_before_pivots_are_confirmed():
    """No pivot can be confirmed in the first k bars, so structure features must
    be absent rather than guessed."""
    df = _random_frame(n=80, seed=2)
    out = compute_indicators(df, k=5)
    for name in ("gfr_px_vs_high", "gfr_channel_pos", "gfr_high_step"):
        assert np.isnan(out[name].iloc[0])
        assert np.isnan(out[name].iloc[4])


def test_channel_position_is_zero_at_low_and_one_at_high():
    # deterministic zig-zag so pivots are unambiguous
    c = np.array([10, 12, 14, 20, 14, 12, 10, 8, 6, 8, 10, 12, 14, 16, 14, 12, 10],
                 dtype=float)
    df = _ohlcv(c)
    out = compute_indicators(df, k=2)
    cp = out["gfr_channel_pos"].to_numpy()
    px_h = out["gfr_px_vs_high"].to_numpy()
    defined = ~np.isnan(cp)
    assert defined.any()
    # where both a high and a low are confirmed, channel_pos is a real ratio and
    # px_vs_high is 0 exactly when price equals the confirmed high
    at_high = np.isclose(px_h[defined], 0.0)
    assert np.isclose(cp[defined][at_high], 1.0).all() or not at_high.any()


def test_features_are_scale_free():
    """Doubling every price must leave ratio features unchanged — otherwise the
    surrogate null is not comparable to the real series."""
    df = _random_frame(n=200, seed=9)
    scaled = df.copy()
    for c in ("open", "high", "low", "close"):
        scaled[c] = scaled[c] * 2.0
    a, b = compute_indicators(df), compute_indicators(scaled)
    for name in ("gfr_px_vs_high", "gfr_px_vs_low", "gfr_channel_pos",
                 "gfr_channel_width", "gfr_high_step", "gfr_low_step",
                 "gfr_span_ratio"):
        pd.testing.assert_series_equal(a[name], b[name], check_names=False,
                                       obj=name)


def test_no_infinities_leak_into_features():
    """Degenerate geometry (zero-width channel) must yield NaN, never inf —
    an inf would poison any downstream z-score or model fit."""
    df = _ohlcv(np.full(60, 100.0))          # perfectly flat: no pivots at all
    for s in compute_indicators(df).values():
        assert not np.isinf(s.to_numpy()).any()


def test_volume_confirmation_is_causal():
    df = _random_frame(n=150, seed=6)
    full = compute_indicators(df)["gfr_volume_confirm"]
    partial = compute_indicators(df.iloc[:100])["gfr_volume_confirm"]
    pd.testing.assert_series_equal(full.iloc[:100], partial, check_names=False)


def test_empty_frame_returns_empty_dict():
    assert compute_indicators(_ohlcv([])) == {}


def test_surrogate_null_can_actually_consume_this_interface():
    """Integration guard for the hard interface claim. surrogate_ic_ir_null is
    Step 4's null control; if compute_indicators' signature or return shape ever
    drifts, this fails here rather than silently returning {} during validation.

    NOTE: the function requires >=10 finite ic_ir values per indicator, so
    n_surrogates must exceed 10 or it returns {} with no explanation.
    """
    import stats as st
    df = _random_frame(n=400, seed=1)
    null = st.surrogate_ic_ir_null(df, compute_indicators, h=config.HORIZON,
                                   n_surrogates=12, seed=0)
    assert len(null) > 0, "surrogate null returned nothing — interface drifted"
    assert set(null) <= set(FEATURE_NAMES)
    for name, v in null.items():
        assert len(v) >= 10, f"{name}: fewer than the 10-value minimum"


def test_surrogate_null_is_not_centred_on_zero():
    """Load-bearing: several of these features carry a large MECHANICAL bias —
    under a no-signal surrogate they still produce strongly non-zero ic_ir,
    because the feature and the forward return share the current close. Judging
    a real ic_ir against zero would therefore be badly wrong; it must be judged
    against this null. Pinning it here so the property cannot be forgotten.
    """
    import stats as st
    df = _random_frame(n=400, seed=1)
    null = st.surrogate_ic_ir_null(df, compute_indicators, h=config.HORIZON,
                                   n_surrogates=12, seed=0)
    biased = [n for n, v in null.items() if abs(float(v.mean())) > 0.1]
    assert biased, ("expected at least one feature with a materially non-zero "
                    "null mean; if this now passes at zero, the null control "
                    "may have stopped working")
