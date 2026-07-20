"""Step 3 tests — XGBoost baseline and the frozen-model null interface.

The two load-bearing tests are `test_closure_delegates_to_shared_feature_builder`
and `test_model_is_frozen_never_refits_during_scoring`. Both guard failures that
would produce numbers rather than errors, which is the dangerous kind.
"""
import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

# xgboost/sklearn live in requirements-ml.txt, deliberately OUT of the core
# install (the Feishu bot never imports ml_patterns/). Without this guard a
# core-only environment reports errors for missing optional extras, which reads
# as a broken suite rather than an absent add-on.
pytest.importorskip("xgboost", reason="requirements-ml.txt not installed")
pytest.importorskip("sklearn", reason="requirements-ml.txt not installed")

from ml_patterns.features import geometric
from ml_patterns.models import baseline
from ml_patterns.models.baseline import (
    fit_baseline, make_model_indicator, FittedBaseline, MODEL_PRED,
)


def _frame(n=600, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.015, n))
    idx = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99, "close": c,
                         "volume": rng.integers(1_000, 9_000, n).astype(float)},
                        index=idx)


@pytest.fixture(scope="module")
def fitted():
    return fit_baseline(_frame(), seed=0)


def test_fit_returns_a_frozen_description_of_its_inputs(fitted):
    assert isinstance(fitted, FittedBaseline)
    assert fitted.feature_names == tuple(sorted(geometric.FEATURE_NAMES))
    assert fitted.n_train_rows >= 50
    assert fitted.train_end_pos == int(600 * config.TRAIN_FRAC)


def test_closure_has_the_shape_surrogate_null_consumes(fitted):
    out = make_model_indicator(fitted)(_frame())
    assert isinstance(out, dict) and set(out) == {MODEL_PRED}
    s = out[MODEL_PRED]
    assert isinstance(s, pd.Series) and s.name == MODEL_PRED
    assert s.notna().sum() > 0


def test_closure_delegates_to_shared_feature_builder(fitted, monkeypatch):
    """LOAD-BEARING. The closure must call features.geometric.compute_indicators,
    not reimplement construction. If it ever forks, training and null-testing
    would build features differently and the comparison would be silently
    invalid — no error, just meaningless numbers.

    Proven by perturbing the shared builder: if the closure delegates, its output
    MUST change.
    """
    df = _frame()
    before = make_model_indicator(fitted)(df)[MODEL_PRED]

    real = geometric.compute_indicators

    def perturbed(d, k=geometric.DEFAULT_K):
        feats = real(d, k=k)
        return {n: s * 0.0 + 1.0 for n, s in feats.items()}   # constant features

    monkeypatch.setattr(geometric, "compute_indicators", perturbed)
    after = make_model_indicator(fitted)(df)[MODEL_PRED]

    assert not np.allclose(before.dropna().to_numpy(),
                           after.dropna().to_numpy()[:before.notna().sum()]), \
        "closure output did not change when the shared feature builder did — " \
        "it is not delegating"


def test_model_is_frozen_never_refits_during_scoring(fitted):
    """LOAD-BEARING. The null must vary only the price path. If scoring refitted,
    it would answer 'does this training procedure manufacture IC on arbitrary
    data?' — a different, far more expensive question."""
    calls = []
    original_fit = fitted.model.fit
    fitted.model.fit = lambda *a, **k: calls.append(1)   # type: ignore[method-assign]
    try:
        ind = make_model_indicator(fitted)
        for seed in range(4):
            ind(_frame(n=400, seed=seed + 10))
        assert calls == [], "model was refitted during scoring"
    finally:
        fitted.model.fit = original_fit                  # type: ignore[method-assign]


def test_closure_captures_the_fitted_model_not_a_copy(fitted):
    """The model must live in the closure, never be rebuilt per call. Inspect the
    closure cells directly rather than asserting something vacuously true."""
    ind = make_model_indicator(fitted)
    captured = [c.cell_contents for c in (ind.__closure__ or ())]
    assert any(c is fitted for c in captured), \
        "closure does not capture the fitted object"
    # and two closures over the same fit agree exactly
    df = _frame(n=400, seed=1)
    pd.testing.assert_series_equal(
        make_model_indicator(fitted)(df)[MODEL_PRED],
        make_model_indicator(fitted)(df)[MODEL_PRED])


def test_model_pred_is_truncation_invariant(fitted):
    """Predictions at bar T must not change when later bars arrive — the feature
    inputs are causal, so the output must inherit that."""
    df = _frame(n=500, seed=3)
    ind = make_model_indicator(fitted)
    full = ind(df)[MODEL_PRED]
    for cut in (250, 400):
        partial = ind(df.iloc[:cut])[MODEL_PRED]
        a, b = full.iloc[:cut], partial
        both = a.notna() & b.notna()
        np.testing.assert_allclose(a[both].to_numpy(), b[both].to_numpy(), rtol=1e-6)


def test_predictions_are_deterministic(fitted):
    df = _frame(n=400, seed=5)
    ind = make_model_indicator(fitted)
    a, b = ind(df)[MODEL_PRED], ind(df)[MODEL_PRED]
    pd.testing.assert_series_equal(a, b)


def test_training_purges_rows_overlapping_the_holdout(fitted):
    """No training row's forward window may reach into the held-out block."""
    n, h = 600, config.HORIZON
    train_end = int(n * config.TRAIN_FRAC)
    # purge + embargo(=h) means the last usable row is train_end - h - ... ,
    # so the count must be strictly below a naive cut at train_end.
    assert fitted.n_train_rows < train_end
    assert fitted.n_train_rows <= train_end - h


def test_surrogate_null_consumes_the_frozen_closure(fitted):
    """The whole point of the factory shape: score the MODEL against a surrogate
    null using the same machinery as its inputs."""
    import stats as st
    df = _frame(n=500, seed=8)
    null = st.surrogate_ic_ir_null(df, make_model_indicator(fitted),
                                   h=config.HORIZON, n_surrogates=12, seed=0)
    assert set(null) == {MODEL_PRED}, "frozen closure not consumable by the null"
    assert len(null[MODEL_PRED]) >= 10


def test_fit_rejects_frames_too_small_to_train_honestly():
    with pytest.raises(ValueError):
        fit_baseline(_frame(n=60))
    with pytest.raises(ValueError):
        fit_baseline(_frame(n=0))


def test_feature_order_is_pinned_so_a_frozen_model_sees_stable_inputs(fitted):
    """A frozen model indexes features positionally; reordering them would feed
    the wrong column to the wrong split without raising."""
    X, names = baseline._feature_matrix(_frame(n=300), fitted.k, fitted.feature_names)
    assert names == fitted.feature_names
    assert X.shape[1] == len(fitted.feature_names)


def test_missing_feature_raises_rather_than_silently_scoring(fitted):
    """If the builder stops producing a feature the model was fitted on, that
    must fail loudly — a silently-dropped column would shift every later one."""
    with pytest.raises(KeyError):
        baseline._feature_matrix(_frame(), fitted.k, ("nope_missing",))
