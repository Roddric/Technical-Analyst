# Indicator Council — Design Spec

**Date:** 2026-07-15
**Status:** Approved (brainstorm), pending implementation plan

## One-line

Each day, for each asset, classify the regime, run several *decorrelated
personality-sets* of technical indicators, weight each set by its **proven
out-of-sample IC**, combine the sets **mechanically** into a direction +
conviction, apply **rule-based** risk to produce concrete levels, and have an
LLM narrate the result. No rhetoric touches the numbers.

## Motivation

The predecessor project (`Work/ta-flat-backtest`) stalled on statistical-power
problems: per-asset IC is underpowered, and narrative/argument-driven selection
overfits. This project inverts the emphasis — **measured evidence sets the
weights; the LLM only explains** — and builds an A/B track record so we can
prove whether the LLM debate adds anything at all.

## Goals

- Produce a daily, human-readable **analysis + trading plan** per asset for
  decision-support (no automated execution).
- Direction and conviction are a **deterministic** function of out-of-sample
  evidence weights — fully reproducible.
- Every number in the plan (entry/stop/target/size) is **rule-derived**, never
  invented by the LLM.
- Build the **A/B comparison** (mechanical evidence arm vs. rhetoric debate arm)
  into v1 so "try both, see which is better" is measurable from day one.

## Scope note: single named stocks

The 14-asset basket is only the default batch universe. The system must also run
on a **specific stock** on demand. `analyze_asset(df, ticker)` is already
ticker-agnostic — it works on any OHLCV frame — so a single stock is a
first-class input. The only missing piece is a **data path for arbitrary
tickers** (the current `load_asset` only knows the cached basket); add a
fetch/loader (e.g. yfinance → same lowercase OHLCV schema) as a near-term item.
For a one-off stock, call `analyze_asset(..., allowed=None)` (marginal t-gate);
grid-FDR only applies when scoring a batch together.

## Non-goals

- No automated/live execution, no broker integration.
- No intraday; daily cadence only.
- No regime×sector conditioning in v1 (see Conditioning).

## M1 empirical findings (2026-07-15, mechanical core complete)

Running the 14-asset batch surfaced two predicted limitations — both are the
diagnostics working, not bugs:
- **Effective-N ≈ 1 on most directional calls:** after grid-FDR usually a single
  set survives per asset, so the "council" is a soft pick-the-best. Confirms the
  need to expand the roster to 5–6 genuinely decorrelated sets before claiming
  ensemble benefit (Problem 3).
- **Inter-set signal corr 0.4–0.76 (> 0.6 threshold on several assets):**
  round-robin member assignment does not achieve decorrelation on real data. M2+
  should replace round-robin with an explicit decorrelated-set *selection* step
  (and prefer the error-correlation invariant over the signal one).

## Key decisions (from brainstorm)

| Decision | Choice |
|---|---|
| Output | Decision-support report + rule-derived plan; no execution |
| Universe / cadence | Existing 14-asset universe, once daily |
| Participants | **Personality-sets**: each a full 4-slot bundle (trend+momentum+volatility+volume) |
| Decorrelation | Enforced **between sets** — personalities must carry different information |
| Arbitration | **Statistical**: each set weighted by its OOS IC, not by argument quality |
| Conditioning | **Start coarse** (overall OOS IC); add regime/sector only if it beats baseline OOS |
| Regime | Mechanical bull / bear / sideways classifier, per asset, causal |
| Plan numbers | Rule-derived (k·ATR stop, R·target, vol-scaled size); LLM explains only |
| Final authority | **Mechanical decision, LLM writes it up** (0 LLM authority over direction) |
| LLM debate | Lives in **arm B** only, compared against the mechanical arm A |

## Architecture

### Pipeline (per asset, per day)

```
prices ─► [1 regime: bull/bear/sideways]
       ─► [2 sets: N decorrelated personality bundles, each = trend+mom+vol+volume]
              each set ─► composite signal  +  [3 evidence weight = OOS IC, shrunk]
       ─► [4 arbiter: Σ weightᵢ·signalᵢ → direction + conviction]   (deterministic)
       ─► [5 risk mgr: vol-target size, k·ATR stop, R·target, drawdown throttle, veto]
       ─► [6 plan object: direction, conviction, entry/stop/target/size]
       ─► [7 narrator LLM: explains WHY; invents no number]
       ─► report (Telegram + saved markdown)  ─► [8 scorecard logs it]
```

### Components (each isolated + independently testable)

| module | responsibility | key interface (sketch) |
|---|---|---|
| `regime.py` | mechanical bull/bear/sideways per asset | `classify_regime(df, asof=None) -> Regime(label, features)` |
| `sets.py` | define personality bundles; build each composite; **enforce inter-set decorrelation** | `build_set_signals(df, personalities) -> dict[name, Series]`; `check_decorrelation(signals, thresh) -> report` |
| `evidence.py` | per-set OOS IC (coarse), shrink → weights, cached | `compute_weights(signals, fwd, cutoff) -> dict[name, weight]` |
| `arbiter.py` | weighted combine → direction + conviction (pure, deterministic) | `arbitrate(latest_signals, weights) -> Decision(direction, conviction)` |
| `risk.py` | rule-based size/stop/target/veto | `build_levels(df, decision, cfg) -> Levels(entry, stop, target, size, veto, reason)` |
| `plan.py` | assemble structured plan object | `assemble_plan(asset, regime, decision, levels, contribs) -> Plan` |
| `narrator.py` | LLM prose from the plan; **no numbers invented** | `narrate(plan, debate_ctx=None) -> str` |
| `debate.py` | rhetoric arm: LLM personas argue direction (arm B only) | `run_debate(asset, readings, regime) -> DebateDecision` |
| `scorecard.py` | log runs, score vs realized returns, **compare arm A vs B** | `log_run(...)`, `score(asof) -> metrics_by_arm` |
| `run.py` | daily orchestration over the universe + delivery | `main()` |
| `config.py` | thresholds, lookbacks, personalities, risk params, horizon | dataclass / constants |

### Reuse

- `pandasta_data` — universe + cached prices (`load_asset`, `UNIVERSE`).
- `pandasta_registry` — indicator definitions (`build_candidates`, `compute_candidate`).
- `stats` — IC (`spearman_ic_hac`), `causal_zscore`, composite construction.
- `quant_morning_brief` — LLM client + Telegram delivery pattern (secrets to be
  moved to env vars during integration).

## The A/B (built in from day one)

- **Arm A (mechanical):** evidence weights decide direction/conviction; LLM narrates.
- **Arm B (rhetoric):** LLM debate + discretionary orchestrator decides direction.
- Both emit the **same** rule-derived levels. `scorecard.py` scores both against
  realized forward returns (conviction-vs-realized IC, hit-rate, plan PnL),
  accumulating a daily track record that answers whether debate adds edge.

## Defaults (finalize during implementation)

- **Regime:** long-MA slope + price position → up/down; ADX/range test → sideways.
  Causal, per asset.
- **Sets (starting roster of 3):** *Fast* (short lookbacks), *Slow* (long
  lookbacks), *Contrarian* (mean-reversion-tilted). Each a 4-slot composite;
  per-slot indicators chosen so the three composites are pairwise
  near-uncorrelated (verified as an invariant, redundant ones replaced).
- **Weights:** `wᵢ ∝ max(0, shrink(OOS ICᵢ))`; a set with no OOS edge contributes
  ~0 (the honest-empty lesson, at the set level).
- **Decision horizon:** configurable; default to a short-swing horizon (~5–10
  trading days) rather than the predecessor's 20, TBD in implementation.

## Testing

- **No-lookahead:** regime + all set signals are strictly causal (assert on
  known fixtures).
- **Determinism:** arm A produces an identical `Decision` for identical inputs.
- **Decorrelation invariant:** pairwise |corr| between set signals below threshold.
- **Risk rules:** unit tests for sizing, stop/target, veto conditions.
- **Scorecard math:** IC/hit-rate/PnL computed correctly on synthetic fixtures.

## Milestones

- **M1 — Mechanical core (no LLM):** `regime` + `sets` + decorrelation check +
  `evidence` + `arbiter` + `risk` + `plan`, deterministic end-to-end for one
  asset, then the universe.
- **M2 — Narration + delivery:** `narrator` + report format + Telegram/file out.
- **M3 — Scorecard + Arm B:** `scorecard` track record + `debate` rhetoric arm +
  A/B scoring.

## Open questions (resolve in plan)

1. Exact regime thresholds and the sideways/range test.
2. Final personality roster and per-slot indicator picks that satisfy decorrelation.
3. Shrinkage estimator for OOS IC weights (James–Stein / empirical-Bayes vs simple).
4. Decision horizon default.
5. Scorecard storage (parquet vs sqlite vs jsonl).
