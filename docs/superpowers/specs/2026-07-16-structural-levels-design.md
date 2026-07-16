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

## Component 2 — support/resistance

`support_resistance(df, k=3, lookback=250, cluster_pct=0.0075, max_levels=3)`:

1. Get swing pivots via `_swing_points`.
2. **Cluster** pivots whose prices are within `cluster_pct` of each other into
   zones. Each zone → representative price (mean of member prices), `touches`
   (member count), `last_touch` (most recent member date).
3. Split zones by current price: `supports` (below), `resistances` (above).
4. Rank each side by proximity to current price; keep nearest `max_levels`.
5. Each level: `{price, touches, last_touch, dist_pct}` where `dist_pct` is
   signed `100*(level-price)/price`.

Output:

```json
"support_resistance": {
  "method": "swing pivots k=3 over 250 bars, clustered within 0.75%",
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

1. Over the lookback window, find the extreme swing **high** and swing **low**
   (fall back to raw window high/low if pivots are sparse).
2. **Direction:** if the high's date is more recent than the low's → recent move
   was up-to-that-high preceded by the low, i.e. an **up-swing** (low→high),
   retracements pull **down** from the high. Otherwise a **down-swing**
   (high→low), retracements bounce **up** from the low.
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

- **Swing detection:** synthetic series with hand-placed peaks/troughs →
  assert exact pivot dates/prices; assert edge bars excluded.
- **S/R clustering:** repeated touches at a known price → one zone with correct
  `touches` and `last_touch`; distinct prices → separate zones; correct
  above/below split and `max_levels` cap.
- **Fibonacci math:** known high/low → assert 0.382/0.5/0.618 prices exactly;
  assert direction inference from anchor recency; assert extension prices.
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
| S/R cluster tolerance | 0.75% of price | `structure.py` |
| S/R max levels per side | 3 | `structure.py` |
| Fib retracements | 0.236, 0.382, 0.5, 0.618, 0.786 | `structure.py` |
| Fib extensions | 1.272, 1.618 | `structure.py` |
