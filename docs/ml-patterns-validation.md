# geometric_forward_return — Step 5 validation result

**Date:** 2026-07-21
**Status:** Complete. **Result: the signal does NOT clear the gate.**
**Consequence:** does not advance to Step 6 (export to ta-flat-backtest).

## What was tested

Confirmed-pivot geometry (Step 0) → 11 scale-free structural features (Step 2)
→ XGBoost baseline (Step 3), scored against surrogate nulls (Step 4) and
BH-FDR (Step 5).

## Why the null, not zero

The features carry a large **mechanical bias**: they share the current close with
the forward return, so arithmetic alone produces strongly non-zero `ic_ir`. Under
a no-signal moving-block surrogate:

| feature | null mean `ic_ir` | null sd |
|---|---|---|
| `gfr_px_vs_low` | −0.44 | 0.07 |
| `gfr_px_vs_high` | −0.38 | 0.08 |
| `gfr_channel_pos` | −0.37 | 0.10 |
| `gfr_channel_width` | +0.18 | 0.07 |

Six-plus standard deviations from zero, with no signal present at all. Every
p-value here is therefore **empirical against the feature's own surrogate
distribution**, two-sided about the null mean, using `(1+count)/(1+n)` so a
finite surrogate sample can never yield p=0.

## Pooling

**Operative gate: BH-FDR pooled PER FEATURE across assets.** A deliberate
departure from the grid pooling used by Stage 1
(`ta-flat-backtest/pandasta_set_search.run_stage1`, one family over all tickers ×
slots) and by `evidence.py` (asset × set grid in `run.run_universe`).

Justified by the measured heterogeneity above: BH's threshold is calibrated to
the mixture of true/false hypotheses in whatever family it receives, so pooling a
mostly-null feature with a working one lets the dead weight raise the shared bar
for the assets where the good feature is genuinely working.

Grid pooling is computed and logged as a **diagnostic only** — never a second
gate, never ANDed with the operative one. It exists so the pooling choice is
visible rather than assumed.

Note: `evidence.py`'s grid pooling feeds **per-asset live plan generation**
(which sets may contribute weight to today's plan), not "should this signal
exist universe-wide". Different family, different purpose — not a precedent for
candidate selection.

## Results

### Raw features — 44 hypotheses (11 features × 4 assets)

**0 survive** under per-feature pooling. **0** under grid pooling. Schemes
disagree on **0**, so the pooling question turned out to be moot here.

Best p-value was 0.0323 (`000660.KS` / `gfr_high_step`), short of the BH
threshold. The most instructive rows:

| asset | feature | real `ic_ir` | null mean | p |
|---|---|---|---|---|
| 2330.TW | `gfr_px_vs_low` | −0.2679 | −0.4031 | 0.129 |
| AAPL | `gfr_channel_pos` | −0.2697 | −0.3518 | 0.323 |

Against **zero**, an `ic_ir` of −0.27 reads as a solid directional signal.
Against its own null it is **weaker than mechanical noise**. This is the single
clearest justification for running Step 4 alongside Step 5 rather than after it.

### XGBoost model — cross-asset out-of-sample

Fitted on AAPL (1353 purged/embargoed training rows), evaluated on three assets
it never saw. Model frozen: only the surrogate price path varies.

| asset | real `ic_ir` | null mean | p |
|---|---|---|---|
| NVDA | 0.1152 | 0.1695 | 0.419 |
| 2330.TW | 0.0884 | 0.0558 | 0.645 |
| 000660.KS | 0.1978 | 0.2263 | 0.871 |

**0 survive.** In two of three assets the model's real `ic_ir` is *below* its
null mean — the apparent positive IC is mechanical bias, not skill.

## Conclusion

Confirmed-pivot geometry, as constructed here, does not predict forward returns
beyond what its own construction bias produces — neither feature-by-feature nor
combined by gradient boosting. Per the plan's own rule (Step 6 conditional on
Step 5), it does not export.

## What this does NOT establish

- Not a refutation of chart patterns generally. It tests one specific feature
  set, one horizon (5d), one model class, four assets.
- The confirmation lag (`k` bars) is a real information cost. Geometry may carry
  signal that has decayed by the time it is confirmable — untested here.
- Only 4 assets, so per-feature families have m=4; BH has little room. A wider
  universe would give the operative gate more power.
- A negative result on raw `ic_ir` does not exclude conditional value (e.g.
  regime-dependent), which was an explicit non-goal for v1.
