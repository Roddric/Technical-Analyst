"""Steps 4+5 tests — surrogate null control and IC/FDR validation.

The load-bearing tests are the ones asserting that (a) p-values are measured
against the displaced null rather than zero, and (b) grid pooling never gates.
Both guard failures that would produce plausible numbers rather than errors.
"""
import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

from ml_patterns.validation import evaluate as ev
from ml_patterns.validation.evaluate import (
    FeatureResult, ValidationReport, empirical_p, pool_per_feature, pool_grid,
    validate_universe, evaluate_asset,
)


def _frame(n=400, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.015, n))
    idx = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99, "close": c,
                         "volume": rng.integers(1_000, 9_000, n).astype(float)},
                        index=idx)


def _r(asset, feature, p, real=0.0, mean=0.0):
    return FeatureResult(asset=asset, feature=feature, real_ic_ir=real,
                         null_mean=mean, null_sd=0.1, n_null=50, p_value=p)


# --------------------------- empirical p-value ---------------------------- #

def test_p_is_measured_against_the_null_centre_not_zero():
    """LOAD-BEARING. The null is displaced (~-0.44 for some features). A real
    value sitting exactly ON the displaced null is NO edge and must be
    insignificant, even though it is far from zero."""
    null = np.random.default_rng(0).normal(-0.44, 0.07, 200)
    on_null = empirical_p(-0.44, null)
    at_zero = empirical_p(0.0, null)
    assert on_null > 0.5, "a value at the null centre must not look significant"
    assert at_zero < 0.05, "zero is extreme relative to a null centred at -0.44"


def test_p_is_two_sided_around_the_null_centre():
    null = np.random.default_rng(1).normal(-0.40, 0.05, 200)
    assert empirical_p(-0.70, null) < 0.05      # far below centre
    assert empirical_p(-0.10, null) < 0.05      # far above centre
    assert empirical_p(-0.40, null) > 0.5       # at centre


def test_p_is_never_exactly_zero():
    """(1+count)/(1+n) — a finite surrogate sample cannot justify p=0."""
    null = np.zeros(50)
    assert empirical_p(1e9, null) > 0.0
    assert empirical_p(1e9, null) == pytest.approx(1 / 51)


def test_p_of_empty_or_nonfinite_is_one():
    assert empirical_p(0.5, np.array([])) == 1.0
    assert empirical_p(np.nan, np.random.normal(size=50)) == 1.0


# ------------------------------- pooling ---------------------------------- #

def test_per_feature_pooling_isolates_families():
    """A feature that is null everywhere must not raise the bar for a feature
    that works — that is the entire reason for the departure from grid pooling."""
    good = [_r(f"A{i}", "good", p) for i, p in enumerate([0.001] * 8)]
    dead = [_r(f"A{i}", "dead", p) for i, p in enumerate([0.9] * 40)]
    surv = pool_per_feature(good + dead, q=0.10)
    assert all((f"A{i}", "good") in surv for i in range(8))
    assert not any((f"A{i}", "dead") in surv for i in range(40))


def test_grid_pooling_can_be_more_conservative_than_per_feature():
    """Demonstrates the choice MATTERS: dead hypotheses in the same family drag
    the shared threshold and can suppress genuine survivors."""
    good = [_r(f"A{i}", "good", 0.02) for i in range(4)]
    dead = [_r(f"B{i}", "dead", 0.95) for i in range(60)]
    per_feature = pool_per_feature(good + dead, q=0.10)
    grid = pool_grid(good + dead, q=0.10)
    assert len(per_feature) > len(grid)
    assert grid.issubset(per_feature)


def test_grid_result_never_gates_anything():
    """LOAD-BEARING. Grid pooling is a diagnostic. The report's survivors must
    equal per-feature pooling exactly — never an intersection with the grid."""
    good = [_r(f"A{i}", "good", 0.02) for i in range(4)]
    dead = [_r(f"B{i}", "dead", 0.95) for i in range(60)]
    rep = ValidationReport(results=good + dead,
                           operative_survivors=pool_per_feature(good + dead),
                           diagnostic_grid_survivors=pool_grid(good + dead))
    per_feature = pool_per_feature(good + dead)
    assert rep.operative_survivors == per_feature
    # This fixture is built so grid is a STRICT subset; an implicit AND would
    # therefore shrink the gate. Assert it does not.
    assert rep.diagnostic_grid_survivors < per_feature
    assert rep.operative_survivors != (per_feature & rep.diagnostic_grid_survivors)
    assert len(rep.operative_survivors) > len(rep.diagnostic_grid_survivors)


def test_disagreements_are_surfaced_not_swallowed():
    good = [_r(f"A{i}", "good", 0.02) for i in range(4)]
    dead = [_r(f"B{i}", "dead", 0.95) for i in range(60)]
    rep = ValidationReport(results=good + dead,
                           operative_survivors=pool_per_feature(good + dead),
                           diagnostic_grid_survivors=pool_grid(good + dead))
    assert len(rep.disagreements) > 0
    frame = rep.to_frame()
    assert frame["schemes_disagree"].any()
    # the frame must label which column is the gate
    assert "survives" in frame and "grid_survives_diagnostic" in frame


def test_empty_results_pool_to_nothing():
    assert pool_per_feature([]) == set()
    assert pool_grid([]) == set()


# --------------------------- end-to-end wiring ---------------------------- #

def test_evaluate_asset_rejects_too_few_surrogates_loudly():
    """surrogate_ic_ir_null returns {} below 10 with no explanation; this must
    fail loudly instead of yielding an empty, plausible-looking result."""
    from ml_patterns.features.geometric import compute_indicators
    with pytest.raises(ValueError, match="n_surrogates"):
        evaluate_asset(_frame(), "X", compute_indicators, n_surrogates=5)


def test_validate_universe_end_to_end_on_features():
    from ml_patterns.features.geometric import compute_indicators
    frames = {"A": _frame(n=400, seed=1), "B": _frame(n=400, seed=2)}
    rep = validate_universe(frames, compute_indicators, n_surrogates=12)
    assert len(rep.results) > 0
    df = rep.to_frame()
    assert set(df["asset"]) == {"A", "B"}
    assert (df["p_value"] > 0).all() and (df["p_value"] <= 1).all()
    assert df["n_null"].min() >= 10


def test_real_ic_ir_matches_the_null_computation_path():
    """Real and null ic_ir must be the SAME statistic; if real were computed a
    different way the comparison would be meaningless without erroring."""
    from ml_patterns.features.geometric import compute_indicators
    df = _frame(n=400, seed=3)
    feats = compute_indicators(df)
    name = "gfr_channel_pos"
    close = df["close"].to_numpy("float64")
    manual = st_ic(feats[name], close)
    assert ev.real_ic_ir(feats[name], close, config.HORIZON) == pytest.approx(manual)


def st_ic(series, close):
    import stats as st
    fwd = st.forward_returns(close, config.HORIZON, "log")
    roll = st.rolling_spearman(series.to_numpy("float64"), fwd,
                               ev.DEFAULT_ROLL_WINDOW)
    return st.ic_ir_hac(roll, lag=config.HORIZON)
