# Structural Levels: Support/Resistance + Fibonacci

**Date:** 2026-07-16
**Status:** Approved design, pending implementation plan

## Goal

Enrich the descriptive TA suite that OpenClaw consumes with two structural-level
sections — multi-level **support/resistance** (swing pivots, clustered into
zones) and direction-aware **Fibonacci** retracement/extension levels. Both are
Layer-1 facts (raw value + mechanical position), consistent with the existing
`compute_indicators` contract.

## Scope & non-goals

- **Descriptive only.** Output flows through `indicators.py::compute_indicators`
  → `tools.py` → OpenClaw. The mechanical council (`selection.py`, `arbiter.py`,
  `risk.py`) is **not touched** — direction/conviction and entry/stop/target stay
  deterministic and ATR-derived. No OOS re-validation is triggered.
- The existing `_levels` section (simple 60-bar rolling high/low) **stays** as-is.
  The new sections are additive, not a replacement.
- **Deferred:** updating `prompt.py` so OpenClaw is told the new fields exist.
  This is done as the final step, after code + tests are complete and verified.

## Architecture

New module **`structure.py`** — one coherent unit ("structural price levels")
with a shared swing-detection primitive and two public functions. `indicators.py`
imports it and adds two keys to the `compute_indicators` dict.

```
structure.py
  _swing_points(df, k)          -> list[(date, price, kind)]   # shared primitive
  support_resistance(df, ...)   -> dict                        # public
  fibonacci_levels(df, ...)     -> dict                        # public

indicators.py::compute_indicators(df)
  ... existing keys ...
  "support_resistance": structure.support_resistance(df),
  "fibonacci":          structure.fibonacci_levels(df),
```

`tools.py` needs no change — it passes the `compute_indicators` dict straight
through, and `_clean` already strips non-finite floats.

## Component 1 — swing detection (shared)

`_swing_points(df, k=3, lookback=250)`:

- Restrict to the last `lookback` bars.
- A bar is a **swing high** if its `high` is the strict/≥ max within the window
  of ±`k` bars; a **swing low** if its `low` is the min within ±`k` bars.
- `k=3` gives a 7-bar fractal. Edge bars (first/last `k`) cannot be pivots.
- Returns a list of `(date: Timestamp, price: float, kind: "high"|"low")`,
  chronologically ordered.

### Causal-confirmation invariant (load-bearing)

A ±`k` fractal pivot at bar `t` is confirmed only by the `k` bars **after** it.
Therefore a pivot at `t` must not appear in output produced as-of any date
`< t + k` — using it earlier would be look-ahead. Two concrete consequences,
both mandatory:

- The detection loop uses only bars in `[t-k, t+k]`; a pivot at `t` is emitted
  only once bar `t+k` exists. **The trailing `k` bars are never pivots**, because
  their forward window is incomplete.
- This is the one invariant that can silently corrupt every downstream level, so
  it gets a dedicated test (see Testing): for a fixed series, a pivot at index
  `t` is absent from `_swing_points(df[:t+k])` and present in
  `_swing_points(df[:t+k+1])`. If detection ever reaches beyond `t+k`, or emits a
  trailing-window bar as a pivot, that test fails.

## Component 2 — support/resistance

`support_resistance(df, k=3, lookback=250, cluster_atr=0.5, max_levels=3)`:

1. Get swing pivots via `_swing_points`.
2. **Cluster** pivots whose prices are within `cluster_atr × ATR(14)` of each
   other into zones (ATR-relative, *not* a fixed percent — a fixed 0.75% means
   something completely different on BTC than on ^FTSE). Each zone →
   representative price (mean of member prices), `touches` (member count),
   `last_touch` (most recent member date). If ATR is unavailable (NaN), fall
   back to a fixed 0.75%-of-price tolerance and note it in `method`.
3. Split zones by current price: `supports` (below), `resistances` (above).
4. Rank each side by proximity to current price; keep nearest `max_levels`.
5. Each level: `{price, touches, last_touch, dist_pct}` where `dist_pct` is
   signed `100*(level-price)/price`.

Output:

```json
"support_resistance": {
  "method": "swing pivots k=3 over 250 bars, clustered within 0.5xATR",
  "supports":    [{"price": 0.0, "touches": 3, "last_touch": "2026-05-12", "dist_pct": -2.1}],
  "resistances": [{"price": 0.0, "touches": 2, "last_touch": "2026-06-30", "dist_pct": 3.4}],
  "nearest_support": 0.0,
  "nearest_resistance": 0.0
}
```

Unavailable case (too few pivots / short history):
`{"available": false, "reason": "..."}`.

## Component 3 — Fibonacci

`fibonacci_levels(df, lookback=250)`:

1. **Dominant swing, not most-recent anchor.** Over the lookback window, take the
   chronological pivot sequence and consider every ordered pair `(i, j)`, `i < j`,
   of **opposite kind** (one high, one low). The swing leg is `pivot_i → pivot_j`
   with amplitude `|price_j − price_i|`. Choose the pair of **maximum amplitude**
   (ties broken toward the most recent, i.e. largest `j` then largest `i`). This
   is the "largest high→low or low→high excursion, direction-aware" from the
   approved option-1 text.
   - *Why not recency-of-anchor:* mapping "which raw extreme is more recent" to a
     direction inverts depending on the mapping and, worse, flip-flops between
     bars near a turning point (the two anchors are close in time there) — one day
     bullish, the next bearish on essentially the same chart. Dominant-move keys
     off the largest excursion, so a marginal new pivot can't silently flip the
     grid; only a genuinely larger leg does.
   - *Sparse-pivot fallback:* if fewer than one high **and** one low pivot exist,
     use the raw window high and low as the two anchors, direction from their
     temporal order. This is the degenerate single-leg case; note it in `swing`.
2. **Direction & anchors:** direction is **up-swing** (low→high) if the later
   pivot `j` is the high, **down-swing** (high→low) if `j` is the low.
   `high = max(price_i, price_j)`, `low = min(...)`, with dates attached
   accordingly. Up-swing retracements pull **down** from the high; down-swing
   retracements bounce **up** from the low.
3. Retracement levels between anchors at ratios **0.236, 0.382, 0.5, 0.618,
   0.786**. For an up-swing: `price = high - ratio*(high-low)`. For a down-swing:
   `price = low + ratio*(high-low)`.
4. Extension levels at **1.272, 1.618** projected beyond the swing in the swing
   direction.
5. Tag each level `pos: "above"|"below"` vs current price; report the single
   `nearest_level` with signed `dist_pct`.

Output:

```json
"fibonacci": {
  "swing": {"direction": "up", "high": 0.0, "high_date": "2026-06-01",
            "low": 0.0, "low_date": "2026-03-10", "amplitude_pct": 18.2},
  "retracements": [{"ratio": 0.382, "price": 0.0, "pos": "below"}],
  "extensions":   [{"ratio": 1.272, "price": 0.0, "pos": "above"}],
  "nearest_level": {"ratio": 0.618, "price": 0.0, "dist_pct": -1.3}
}
```

Unavailable case: `{"available": false, "reason": "..."}`.

## Error handling

- Short history or no detectable swings → `{"available": false, "reason": ...}`,
  matching the `_volume` convention. `compute_indicators` still requires ≥200
  bars overall (unchanged); the structural sections degrade gracefully within
  that.
- Every emitted float is finite-guarded (`_last`-style) so `tools.py::_clean`
  never sees a stray NaN/inf.

## Testing — `tests/test_structure.py`

- **Causal confirmation (load-bearing):** for a fixed series with a known pivot
  at index `t`, assert the pivot is **absent** from `_swing_points(df[:t+k])` and
  **present** in `_swing_points(df[:t+k+1])`; assert the trailing `k` bars are
  never returned as pivots. This is the test that catches look-ahead in the
  detection loop — if it passes, the rest is tuning.
- **Swing detection:** synthetic series with hand-placed peaks/troughs →
  assert exact pivot dates/prices; assert edge bars excluded.
- **S/R clustering:** repeated touches at a known price → one zone with correct
  `touches` and `last_touch`; distinct prices → separate zones; correct
  above/below split and `max_levels` cap; ATR-relative tolerance widens/narrows
  clustering as ATR changes, with the fixed-percent fallback when ATR is NaN.
- **Fibonacci math:** known high/low → assert 0.382/0.5/0.618 prices exactly;
  assert extension prices.
- **Fib dominant-swing & stability:** a series whose largest excursion is a
  low→high leg yields `direction: "up"` even when a smaller, more-recent
  down-pivot exists (proves dominant-move beats recency-of-anchor); appending one
  bar that does not create a larger leg must **not** flip `direction`
  (anti-flip-flop regression).
- **Safety:** short (<lookback) and flat (no pivots) series → `available: false`,
  no exceptions, no non-finite floats.

## Wiring (final, deferred)

Add a couple of additive lines to `prompt.py` telling OpenClaw the
`support_resistance` and `fibonacci` fields exist and are Layer-1 facts. Done
only after code + tests pass.

## Defaults summary

| Param | Default | Where |
|-------|---------|-------|
| swing `k` | 3 (7-bar fractal) | `structure.py` |
| lookback | 250 bars | `structure.py` |
| S/R cluster tolerance | `0.5 × ATR(14)` (fallback 0.75% of price if ATR NaN) | `structure.py` |
| S/R max levels per side | 3 | `structure.py` |
| Fib swing selection | max-amplitude opposite-pivot excursion (dominant move) | `structure.py` |
| Fib retracements | 0.236, 0.382, 0.5, 0.618, 0.786 | `structure.py` |
| Fib extensions | 1.272, 1.618 | `structure.py` |

## Known crudeness (logged, not hidden)

- **`cluster_atr` and `k` are fixed constants, not per-asset-tuned.** Since this
  layer is descriptive-only, a suboptimal default costs narration quality, not
  decisions — no validation gate needed. Recorded here so it isn't rediscovered
  as a surprise.
- The ATR-relative cluster tolerance is implemented now (not deferred); the only
  remaining fixed-percent path is the ATR-NaN fallback.
