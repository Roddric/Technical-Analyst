"""Step 3 — XGBoost baseline for the geometric_forward_return signal.

TWO INVARIANTS THIS MODULE EXISTS TO ENFORCE
--------------------------------------------

1. THE MODEL IS FROZEN DURING NULL TESTING.
   `make_model_indicator` returns a closure over an ALREADY-FITTED model. Under
   the surrogate null, only the price path varies; the model is never refitted.
   Refitting per surrogate would answer a different and far more expensive
   question — "does this training procedure manufacture IC on arbitrary data?" —
   instead of the one we need: "does this fitted model's edge survive the same
   mechanical-bias check its inputs got?" The model lives in the closure, never
   in `df`.

2. THE CLOSURE DELEGATES TO THE SHARED FEATURE BUILDER.
   It calls `features.geometric.compute_indicators` — the exact function used to
   build the training matrix. It must never reimplement feature construction.
   Any drift between how training saw features and how the null test builds them
   would invalidate the comparison WITHOUT raising anything: the numbers would
   still appear, and they would be meaningless.

Why the model output needs the null at all: the Step-2 features carry a large
mechanical bias (several average ic_ir near -0.4 under a no-signal surrogate,
because they share the current close with the forward return). A model trained on
biased inputs inherits that bias in its predictions, so `model_pred` must be
scored against its own surrogate null, never against zero.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()

from ml_patterns.features import geometric
from ml_patterns.labeling.geometric_forward_return import (
    forward_return_labels, purge_overlapping,
)

MODEL_PRED = "model_pred"
DEFAULT_K = geometric.DEFAULT_K


@dataclass(frozen=True)
class FittedBaseline:
    """A fitted model plus everything needed to rebuild its inputs identically."""
    model: object
    feature_names: tuple[str, ...]
    k: int
    horizon: int
    train_end_pos: int
    n_train_rows: int


def _feature_matrix(df: pd.DataFrame, k: int,
                    feature_names: tuple[str, ...] | None = None):
    """Features as a 2-D array, via the SHARED builder. Column order is pinned so
    a frozen model always sees its inputs in the order it was fitted on."""
    feats = geometric.compute_indicators(df, k=k)
    if not feats:
        names = tuple(feature_names or ())
        return np.empty((0, len(names))), names
    names = tuple(feature_names) if feature_names else tuple(sorted(feats))
    missing = [n for n in names if n not in feats]
    if missing:
        raise KeyError(f"feature builder did not produce {missing}; "
                       "training and scoring must use the same features")
    X = np.column_stack([feats[n].to_numpy("float64") for n in names])
    return X, names


def fit_baseline(df: pd.DataFrame, horizon: int = config.HORIZON,
                 k: int = DEFAULT_K, train_frac: float = config.TRAIN_FRAC,
                 embargo: int | None = None, seed: int = 0,
                 **xgb_kwargs) -> FittedBaseline:
    """Fit on the TRAIN slice only, with the holdout purged and embargoed.

    Rows whose forward window reaches into the holdout are dropped, not merely
    the holdout rows themselves — overlapping labels are how a plain cut leaks
    across the boundary (see labeling/). `embargo` defaults to `horizon`.
    """
    from xgboost import XGBRegressor

    if df is None or len(df) == 0:
        raise ValueError("cannot fit on an empty frame")
    embargo = horizon if embargo is None else embargo
    n = len(df)
    train_end = int(n * train_frac)

    X, names = _feature_matrix(df, k)
    labels = forward_return_labels(df, horizon=horizon)
    y = labels["fwd_return"].to_numpy("float64")

    # Treat everything from train_end onward as the held-out block, then purge
    # the training rows whose forward windows touch it.
    keep = purge_overlapping(labels, test_start_pos=train_end,
                             test_end_pos=n - 1, horizon=horizon, embargo=embargo)
    finite = np.isfinite(X).all(axis=1) & np.isfinite(y)
    rows = keep & finite
    if rows.sum() < 50:
        raise ValueError(f"only {int(rows.sum())} usable training rows after "
                         "purge/embargo — need at least 50")

    params = {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05,
              "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0,
              "random_state": seed, "n_jobs": 1}
    params.update(xgb_kwargs)
    model = XGBRegressor(**params)
    model.fit(X[rows], y[rows])

    return FittedBaseline(model=model, feature_names=names, k=k, horizon=horizon,
                          train_end_pos=train_end, n_train_rows=int(rows.sum()))


def make_model_indicator(fitted: FittedBaseline):
    """Factory: frozen model -> `compute_indicators(df) -> {"model_pred": Series}`.

    The returned closure has exactly the shape `stats.surrogate_ic_ir_null`
    consumes, so the model's own output can be scored against a surrogate null
    using the same machinery as its inputs — with the model held fixed and only
    the price path varying.
    """
    def compute_indicators(df: pd.DataFrame) -> dict[str, pd.Series]:
        if df is None or len(df) == 0:
            return {}
        # Delegate to the SHARED builder — never reimplement feature construction.
        X, _ = _feature_matrix(df, fitted.k, fitted.feature_names)
        if X.size == 0:
            return {}
        pred = np.full(len(df), np.nan)
        rows = np.isfinite(X).all(axis=1)
        if rows.any():
            pred[rows] = fitted.model.predict(X[rows])
        return {MODEL_PRED: pd.Series(pred, index=df.index, name=MODEL_PRED)}

    return compute_indicators
