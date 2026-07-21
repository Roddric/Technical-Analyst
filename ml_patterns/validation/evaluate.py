"""Steps 4+5 — surrogate null control and IC/FDR validation.

These are ONE computation, not two phases. The null is not a post-hoc sanity
check on a number already believed; it is the reference the number is measured
against in the first place.

WHY THE NULL IS THE REFERENCE, NOT ZERO
---------------------------------------
Measured on real data, the Step-2 features carry a large mechanical bias. Under
a no-signal surrogate, `gfr_px_vs_low` averages ic_ir -0.44 (sd 0.07),
`gfr_px_vs_high` -0.38, `gfr_channel_pos` -0.37 — six-plus sd from zero. They
share the current close with the forward return, so arithmetic alone produces
those values. Testing a real ic_ir against zero would "discover" a strong edge
in every one of them. Every p-value here is therefore EMPIRICAL against that
feature's own surrogate distribution.

POOLING: WHAT IS DECIDED BY WHAT
--------------------------------
The operative gate is BH-FDR pooled PER FEATURE across assets. That is a
deliberate departure from the grid pooling used by Stage 1
(ta-flat-backtest/pandasta_set_search.run_stage1, which pools all tickers x
slots into one family) and by evidence.py (which pools the asset x set grid in
run.run_universe).

Justification is measured, not stylistic: null bias ranges from -0.44 to +0.18
across these features. BH's threshold is calibrated to the mixture of true and
false hypotheses in whatever family it is handed, so lumping a mostly-null
feature together with one carrying real signal lets the dead weight raise the
shared bar for the assets where the good feature genuinely works. Per-feature
pooling lets each feature's own discovery rate set its own threshold.

Grid pooling is ALSO computed and reported — as a DIAGNOSTIC ONLY. It is not a
second gate. A feature does not need to clear both; nothing may turn the pair
into an implicit AND. It exists so the choice of family is visible rather than
assumed, and so a disagreement between the two is seen rather than hidden.

Note on the different question evidence.py answers: its grid pooling feeds
per-asset live plan generation (which sets may contribute weight to today's plan
for this asset), not "should this signal exist universe-wide". Different family,
different purpose — its strictness there is not a precedent for candidate
selection here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import stats as st

DEFAULT_ROLL_WINDOW = 63
DEFAULT_N_SURROGATES = 50


@dataclass(frozen=True)
class FeatureResult:
    asset: str
    feature: str
    real_ic_ir: float
    null_mean: float
    null_sd: float
    n_null: int
    p_value: float          # empirical, two-sided, against this feature's null


@dataclass
class ValidationReport:
    results: list[FeatureResult] = field(default_factory=list)
    operative_survivors: set = field(default_factory=set)   # per-feature pooling
    diagnostic_grid_survivors: set = field(default_factory=set)  # NOT a gate

    @property
    def disagreements(self) -> set:
        """Keys the two schemes treat differently. Reported, never acted on."""
        return self.operative_survivors ^ self.diagnostic_grid_survivors

    def to_frame(self) -> pd.DataFrame:
        rows = []
        for r in self.results:
            key = (r.asset, r.feature)
            rows.append({
                "asset": r.asset, "feature": r.feature,
                "real_ic_ir": r.real_ic_ir, "null_mean": r.null_mean,
                "null_sd": r.null_sd, "n_null": r.n_null, "p_value": r.p_value,
                "survives": key in self.operative_survivors,          # THE gate
                "grid_survives_diagnostic": key in self.diagnostic_grid_survivors,
                "schemes_disagree": key in self.disagreements,
            })
        return pd.DataFrame(rows)


def real_ic_ir(indicator: pd.Series, close: np.ndarray, h: int,
               roll_window: int = DEFAULT_ROLL_WINDOW) -> float:
    """Real ic_ir, computed EXACTLY as surrogate_ic_ir_null computes its own —
    same rolling_spearman, same ic_ir_hac, same lag. Any divergence here would
    compare two different statistics and would not raise."""
    fwd = st.forward_returns(close, h, "log")
    roll = st.rolling_spearman(indicator.to_numpy("float64"), fwd, roll_window)
    return st.ic_ir_hac(roll, lag=h)


def empirical_p(real: float, null: np.ndarray) -> float:
    """Two-sided empirical p: how extreme is `real` relative to its own null?

    Centred on the NULL MEAN, not zero — the whole point is that the null is
    displaced. Uses the (1 + count) / (1 + n) estimator so p is never exactly 0,
    which would overstate significance from a finite surrogate sample.
    """
    null = np.asarray(null, dtype="float64")
    null = null[np.isfinite(null)]
    if null.size == 0 or not np.isfinite(real):
        return 1.0
    centre = null.mean()
    at_least_as_extreme = np.abs(null - centre) >= abs(real - centre)
    return float((1 + at_least_as_extreme.sum()) / (1 + null.size))


def evaluate_asset(df: pd.DataFrame, asset: str, compute_indicators,
                   h: int = config.HORIZON,
                   roll_window: int = DEFAULT_ROLL_WINDOW,
                   n_surrogates: int = DEFAULT_N_SURROGATES,
                   seed: int = 0) -> list[FeatureResult]:
    """Real vs surrogate-null ic_ir for every feature on one asset.

    `compute_indicators` is the shared interface: either the Step-2 feature
    builder or a FROZEN model closure from models.make_model_indicator. Under
    the null only the price path varies — the model is never refitted.
    """
    if df is None or len(df) == 0:
        return []
    feats = compute_indicators(df)
    if not feats:
        return []
    # surrogate_ic_ir_null silently returns {} below 10 finite values per
    # indicator; make that a loud precondition rather than an empty result.
    if n_surrogates < 10:
        raise ValueError("n_surrogates must be >= 10: surrogate_ic_ir_null "
                         "requires 10 finite ic_ir values and returns {} below it")

    null = st.surrogate_ic_ir_null(df, compute_indicators, h=h,
                                   roll_window=roll_window,
                                   n_surrogates=n_surrogates, seed=seed)
    close = df["close"].to_numpy("float64")
    out = []
    for name, series in feats.items():
        nv = np.asarray(null.get(name, []), dtype="float64")
        nv = nv[np.isfinite(nv)]
        real = real_ic_ir(series, close, h, roll_window)
        out.append(FeatureResult(
            asset=asset, feature=name, real_ic_ir=float(real),
            null_mean=float(nv.mean()) if nv.size else float("nan"),
            null_sd=float(nv.std()) if nv.size else float("nan"),
            n_null=int(nv.size), p_value=empirical_p(real, nv)))
    return out


def _bh(pvals: dict, q: float) -> set:
    """Benjamini-Hochberg over one family; returns surviving keys."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    if m == 0:
        return set()
    cutoff = 0
    for i, (_, p) in enumerate(items, start=1):
        if p <= (i / m) * q:
            cutoff = i
    return {k for i, (k, _) in enumerate(items, start=1) if i <= cutoff}


def pool_per_feature(results: list[FeatureResult], q: float = config.FDR_Q) -> set:
    """THE OPERATIVE GATE. One BH family per feature, across assets."""
    by_feature: dict[str, dict] = {}
    for r in results:
        by_feature.setdefault(r.feature, {})[(r.asset, r.feature)] = r.p_value
    survivors: set = set()
    for fam in by_feature.values():
        survivors |= _bh(fam, q)
    return survivors


def pool_grid(results: list[FeatureResult], q: float = config.FDR_Q) -> set:
    """DIAGNOSTIC ONLY — never a gate, never ANDed with the operative one.
    Single BH family over the whole asset x feature grid, matching Stage 1 and
    evidence.py, so the effect of the pooling choice is visible."""
    return _bh({(r.asset, r.feature): r.p_value for r in results}, q)


def validate_universe(frames: dict, compute_indicators,
                      h: int = config.HORIZON,
                      roll_window: int = DEFAULT_ROLL_WINDOW,
                      n_surrogates: int = DEFAULT_N_SURROGATES,
                      q: float = config.FDR_Q, seed: int = 0) -> ValidationReport:
    """Full validation across a {asset: df} mapping.

    Only `operative_survivors` decides what advances to Step 6.
    `diagnostic_grid_survivors` is logged for comparison and must not gate.
    """
    results: list[FeatureResult] = []
    for asset, df in frames.items():
        results.extend(evaluate_asset(df, asset, compute_indicators, h,
                                      roll_window, n_surrogates, seed))
    return ValidationReport(
        results=results,
        operative_survivors=pool_per_feature(results, q),
        diagnostic_grid_survivors=pool_grid(results, q))
