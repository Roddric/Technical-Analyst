# Structural Levels (Support/Resistance + Fibonacci) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-level swing-pivot support/resistance and dominant-swing Fibonacci levels to the descriptive TA suite that OpenClaw consumes, as two new keys on `compute_indicators`.

**Architecture:** One new module `structure.py` holds a shared swing-pivot primitive (`_swing_points`) and two public functions (`support_resistance`, `fibonacci_levels`). `indicators.py::compute_indicators` gains two keys. The mechanical council (`selection.py`/`arbiter.py`/`risk.py`) is never touched. `prompt.py` wiring is the deferred final task.

**Tech Stack:** Python 3, pandas, numpy, pandas_ta (loaded via `config.ensure_reuse_on_path()`), pytest.

**Spec:** `docs/superpowers/specs/2026-07-16-structural-levels-design.md`

## Global Constraints

- **Descriptive only.** `structure.py` must never be imported by `selection.py`, `arbiter.py`, `risk.py`, `evidence.py`, or `run.py`. It is consumed only through `indicators.py::compute_indicators`.
- **Finite-guard every emitted float.** No NaN/inf may reach output — `tools.py::_clean` should never have to strip a structural-level value. Missing data → `{"available": false, "reason": ...}` (the `_volume` convention).
- **pandas_ta access:** `import config; config.ensure_reuse_on_path(); import pandas_ta`. ATR is `df.ta.atr(length=14)`.
- **Run tests from the repo root** `Work/indicator-council/` with `pytest` (config: `pytest.ini`, `pythonpath=.`, `addopts=-q`).
- **Fixed module constants** (from the spec defaults): `SWING_K=3`, `LOOKBACK=250`, `CLUSTER_ATR=0.5`, `FALLBACK_CLUSTER_PCT=0.0075`, `SR_MAX_LEVELS=3`, `FIB_RETR=(0.236,0.382,0.5,0.618,0.786)`, `FIB_EXT=(1.272,1.618)`.
- **Swing tie rule:** left-loose / right-strict (pivot on the last bar of a plateau).
- Prices rounded to 2 dp, `dist_pct`/`amplitude_pct` to 2 dp — matching the existing `_levels` convention in `indicators.py`.

## File Structure

- **Create** `structure.py` — swing detection + S/R + Fibonacci. Sole owner of structural-level logic.
- **Create** `tests/test_structure.py` — all unit tests for the module.
- **Modify** `indicators.py` — import `structure`, add two keys to `compute_indicators`.
- **Modify** `prompt.py` — deferred; two additive lines telling OpenClaw the fields exist (Task 5, after 1–4 verified).

---

### Task 1: `structure.py` scaffold + `_swing_points`

**Files:**
- Create: `structure.py`
- Test: `tests/test_structure.py`

**Interfaces:**
- Consumes: nothing (leaf module).
- Produces:
  - `_atr(df: pd.DataFrame) -> float` — last ATR(14), or `float("nan")`.
  - `_swing_points(df: pd.DataFrame, k: int = 3, lookback: int = 250) -> list[tuple[pd.Timestamp, float, str]]` — chronological `(date, price, kind)` where `kind in {"high","low"}`.
  - Module constants listed in Global Constraints.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_structure.py`:

```python
import json
import math

import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

import structure


def _frame(highs, lows=None, closes=None, start="2021-01-01"):
    """Flat-OHLC-friendly builder. Defaults low=close=high so extrema are clean."""
    n = len(highs)
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows if lows is not None else highs, dtype=float)
    closes = np.asarray(closes if closes is not None else highs, dtype=float)
    idx = pd.bdate_range(start, periods=n)
    return pd.DataFrame(
        {"open": closes, "high": highs, "low": lows, "close": closes,
         "volume": np.full(n, 1000.0)},
        index=idx,
    )


def _zigzag(anchors, seg=6):
    """Piecewise-linear path through `anchors`; each interior anchor is a clean
    k=3 pivot. Anchor i sits at position i*seg. Flat OHLC (high=low=close)."""
    vals = []
    for a, b in zip(anchors[:-1], anchors[1:]):
        seg_vals = np.linspace(a, b, seg + 1)
        vals.extend(seg_vals[:-1])          # drop shared endpoint
    vals.append(anchors[-1])
    return _frame(vals)


def test_swing_points_single_peak_and_trough():
    df = _frame([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])   # apex at index 5
    piv = structure._swing_points(df, k=3)
    highs = [(d, p) for d, p, kind in piv if kind == "high"]
    assert len(highs) == 1
    assert highs[0][0] == df.index[5]
    assert highs[0][1] == 6.0


def test_swing_points_causal_confirmation():
    df = _frame([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])   # apex t=5, k=3
    t, k = 5, 3
    before = structure._swing_points(df.iloc[: t + k], k=k)      # df[:8]
    after = structure._swing_points(df.iloc[: t + k + 1], k=k)   # df[:9]
    assert all(d != df.index[t] for d, _, _ in before)          # not yet confirmed
    assert any(d == df.index[t] for d, _, _ in after)           # confirmed at t+k


def test_swing_points_trailing_k_never_pivots():
    df = _frame([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
    k = 3
    piv = structure._swing_points(df, k=k)
    trailing = set(df.index[-k:])
    assert all(d not in trailing for d, _, _ in piv)


def test_swing_high_flat_top_picks_rightmost():
    # plateau at positions 3,4 (value 5); constant lows -> no low pivots
    df = _frame(highs=[1, 2, 3, 5, 5, 4, 3, 2, 1], lows=[0.5] * 9)
    piv = structure._swing_points(df, k=3)
    highs = [d for d, _, kind in piv if kind == "high"]
    assert len(highs) == 1
    assert highs[0] == df.index[4]      # rightmost bar of the plateau


def test_swing_low_flat_bottom_picks_rightmost():
    # trough plateau at positions 3,4 (value 5); constant highs -> no high pivots
    df = _frame(highs=[9] * 9, lows=[9, 8, 7, 5, 5, 6, 7, 8, 9])
    piv = structure._swing_points(df, k=3)
    lows = [d for d, _, kind in piv if kind == "low"]
    assert len(lows) == 1
    assert lows[0] == df.index[4]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_structure.py -q`
Expected: FAIL / ERROR — `AttributeError: module 'structure' has no attribute '_swing_points'` (module doesn't exist yet).

- [ ] **Step 3: Write `structure.py` with constants, `_atr`, `_swing_points`**

Create `structure.py`:

```python
"""Structural price levels — swing-pivot support/resistance and dominant-swing
Fibonacci retracement/extension levels.

DESCRIPTIVE ONLY (Layer-1 facts). Consumed by OpenClaw via
indicators.py::compute_indicators. The mechanical council (selection/arbiter/
risk) must never import this module."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import pandas_ta  # noqa: F401  registers the .ta accessor

SWING_K = 3
LOOKBACK = 250
CLUSTER_ATR = 0.5
FALLBACK_CLUSTER_PCT = 0.0075
SR_MAX_LEVELS = 3
FIB_RETR = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXT = (1.272, 1.618)


def _atr(df: pd.DataFrame) -> float:
    a = df.ta.atr(length=14)
    if a is None or len(a) == 0:
        return float("nan")
    v = a.iloc[-1]
    return float(v) if np.isfinite(v) else float("nan")


def _last_close(df: pd.DataFrame) -> float:
    c = df["close"].dropna()
    return float(c.iloc[-1]) if len(c) else float("nan")


def _swing_points(df: pd.DataFrame, k: int = SWING_K,
                  lookback: int = LOOKBACK) -> list[tuple[pd.Timestamp, float, str]]:
    """Fractal pivots over the last min(lookback, len(df)) bars.

    Swing high: high[t] >= max(left k) and high[t] > max(right k)   (left-loose,
    right-strict). Swing low is the mirror. A pivot at t is only emitted once its
    k forward bars exist, so the trailing k bars are never pivots (no look-ahead).
    """
    win = df.tail(min(lookback, len(df)))
    highs = win["high"].to_numpy(dtype=float)
    lows = win["low"].to_numpy(dtype=float)
    idx = win.index
    out: list[tuple[pd.Timestamp, float, str]] = []
    for t in range(k, len(win) - k):
        h, lo = highs[t], lows[t]
        if np.isfinite(h) and h >= highs[t - k:t].max() and h > highs[t + 1:t + k + 1].max():
            out.append((idx[t], float(h), "high"))
        if np.isfinite(lo) and lo <= lows[t - k:t].min() and lo < lows[t + 1:t + k + 1].min():
            out.append((idx[t], float(lo), "low"))
    out.sort(key=lambda p: p[0])
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_structure.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add structure.py tests/test_structure.py
git commit -m "feat(structure): swing-pivot detection with causal confirmation and pinned tie rule"
```

---

### Task 2: `support_resistance`

**Files:**
- Modify: `structure.py`
- Test: `tests/test_structure.py`

**Interfaces:**
- Consumes: `_swing_points`, `_atr`, `_last_close` from Task 1.
- Produces: `support_resistance(df, k=3, lookback=250, cluster_atr=0.5, max_levels=3) -> dict` with either `{"available": False, "reason": str}` or keys `method, supports, resistances, nearest_support, nearest_resistance`. Each level: `{"price", "touches", "last_touch", "dist_pct"}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_structure.py`:

```python
def test_sr_clusters_repeated_touches_into_one_zone():
    # two swing highs at ~150 (positions 6 and 18), lows near 100, current ~120
    df = _zigzag([120, 100, 150, 100, 150, 100, 120], seg=6)
    out = structure.support_resistance(df, cluster_atr=5.0)
    assert out["available"] is not False
    res = out["resistances"]
    # the two 150 highs collapse into a single zone with touches >= 2
    assert any(abs(z["price"] - 150) < 2 and z["touches"] >= 2 for z in res)


def test_sr_distinct_prices_stay_separate():
    df = _zigzag([120, 100, 150, 100, 180, 100, 120], seg=6)
    out = structure.support_resistance(df, cluster_atr=0.1)
    prices = sorted(z["price"] for z in out["resistances"])
    assert any(abs(p - 150) < 2 for p in prices)
    assert any(abs(p - 180) < 2 for p in prices)


def test_sr_splits_by_current_price_and_caps_levels():
    df = _zigzag([120, 90, 160, 95, 170, 100, 130], seg=6)
    out = structure.support_resistance(df, cluster_atr=0.1, max_levels=1)
    price = float(df["close"].iloc[-1])
    assert len(out["supports"]) <= 1 and len(out["resistances"]) <= 1
    assert all(z["price"] < price for z in out["supports"])
    assert all(z["price"] > price for z in out["resistances"])


def test_sr_atr_fallback_when_atr_nan(monkeypatch):
    df = _zigzag([120, 100, 150, 100, 150, 100, 120], seg=6)
    monkeypatch.setattr(structure, "_atr", lambda d: float("nan"))
    out = structure.support_resistance(df)
    assert "0.75%" in out["method"] or "ATR unavailable" in out["method"]


def test_sr_unavailable_when_no_pivots():
    df = _frame([100.0] * 300)          # perfectly flat -> no swings
    out = structure.support_resistance(df)
    assert out == {"available": False, "reason": out["reason"]}
    assert out["available"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_structure.py -q`
Expected: FAIL — `AttributeError: module 'structure' has no attribute 'support_resistance'`.

- [ ] **Step 3: Implement `support_resistance`**

Append to `structure.py`:

```python
def _cluster(pivots, tol):
    """Single-linkage over price-sorted pivots: break a zone when the gap to the
    next pivot price exceeds tol. Returns [(rep_price, touches, last_touch)]."""
    if not pivots:
        return []
    ordered = sorted(pivots, key=lambda p: p[1])
    zones = []
    grp = [ordered[0]]
    for piv in ordered[1:]:
        if piv[1] - grp[-1][1] <= tol:
            grp.append(piv)
        else:
            zones.append(grp)
            grp = [piv]
    zones.append(grp)
    out = []
    for grp in zones:
        rep = float(np.mean([p[1] for p in grp]))
        last_touch = max(p[0] for p in grp)
        out.append((round(rep, 2), len(grp), str(last_touch.date())))
    return out


def support_resistance(df: pd.DataFrame, k: int = SWING_K, lookback: int = LOOKBACK,
                       cluster_atr: float = CLUSTER_ATR,
                       max_levels: int = SR_MAX_LEVELS) -> dict:
    price = _last_close(df)
    pivots = _swing_points(df, k=k, lookback=lookback)
    if not pivots or not np.isfinite(price):
        return {"available": False, "reason": "no swing pivots / insufficient history"}

    win_len = min(lookback, len(df))
    atr = _atr(df)
    if np.isfinite(atr) and atr > 0:
        tol = cluster_atr * atr
        tol_desc = f"{cluster_atr}xATR"
    else:
        tol = FALLBACK_CLUSTER_PCT * price
        tol_desc = "0.75% (ATR unavailable)"

    def _level(zone):
        rep, touches, last_touch = zone
        return {"price": rep, "touches": touches, "last_touch": last_touch,
                "dist_pct": round(100 * (rep - price) / price, 2)}

    zones = _cluster(pivots, tol)
    supports = sorted((z for z in zones if z[0] < price), key=lambda z: -z[0])
    resistances = sorted((z for z in zones if z[0] >= price), key=lambda z: z[0])
    sup = [_level(z) for z in supports[:max_levels]]
    res = [_level(z) for z in resistances[:max_levels]]
    return {
        "method": f"swing pivots k={k} over {win_len} bars, clustered within {tol_desc}",
        "supports": sup,
        "resistances": res,
        "nearest_support": sup[0]["price"] if sup else None,
        "nearest_resistance": res[0]["price"] if res else None,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_structure.py -q`
Expected: PASS (10 tests total).

- [ ] **Step 5: Commit**

```bash
git add structure.py tests/test_structure.py
git commit -m "feat(structure): ATR-relative swing-pivot support/resistance zones"
```

---

### Task 3: `fibonacci_levels`

**Files:**
- Modify: `structure.py`
- Test: `tests/test_structure.py`

**Interfaces:**
- Consumes: `_swing_points`, `_last_close` from Task 1.
- Produces: `fibonacci_levels(df, k=3, lookback=250) -> dict` with either `{"available": False, "reason": str}` or keys `swing, retracements, extensions, nearest_level`. `swing = {direction, high, high_date, low, low_date, amplitude_pct, window_bars}`. Each level: `{"ratio", "price", "pos"}`. `nearest_level = {"ratio", "price", "dist_pct"}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_structure.py`:

```python
def test_fib_upswing_exact_math():
    # low 100 @pos6, high 200 @pos12, current 150 @pos18 (last bar)
    df = _zigzag([120, 100, 200, 150], seg=6)
    out = structure.fibonacci_levels(df)
    assert out["swing"]["direction"] == "up"
    assert out["swing"]["high"] == 200.0
    assert out["swing"]["low"] == 100.0
    assert out["swing"]["amplitude_pct"] == 100.0
    r = {lvl["ratio"]: lvl["price"] for lvl in out["retracements"]}
    assert r[0.382] == 161.8
    assert r[0.5] == 150.0
    assert r[0.618] == 138.2
    e = {lvl["ratio"]: lvl["price"] for lvl in out["extensions"]}
    assert e[1.272] == 227.2
    assert e[1.618] == 261.8
    assert out["nearest_level"]["ratio"] == 0.5     # 150 == current price


def test_fib_dominant_swing_beats_recency_and_is_stable():
    # biggest leg is 100->200 (up); a smaller, more-recent 200->180 down leg exists
    df = _zigzag([120, 100, 200, 180, 190], seg=6)
    out = structure.fibonacci_levels(df)
    assert out["swing"]["direction"] == "up"
    # append one bar that does NOT create a larger leg -> direction must not flip
    extra = df.iloc[[-1]].copy()
    extra.index = [df.index[-1] + pd.tseries.offsets.BDay(1)]
    extra.iloc[0, :] = 188.0
    df2 = pd.concat([df, extra])
    assert structure.fibonacci_levels(df2)["swing"]["direction"] == "up"


def test_fib_no_confirmed_swing_returns_unavailable():
    # single tent: one high pivot at apex, zero interior swing lows
    df = _frame(list(range(1, 14)) + list(range(12, 0, -1)))   # up then down
    out = structure.fibonacci_levels(df)
    assert out["available"] is False
    assert "swing" not in out
    assert "both" in out["reason"] or "confirmed swing" in out["reason"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_structure.py -q`
Expected: FAIL — `AttributeError: module 'structure' has no attribute 'fibonacci_levels'`.

- [ ] **Step 3: Implement `fibonacci_levels`**

Append to `structure.py`:

```python
def _dominant_pair(pivots):
    """Max-amplitude opposite-kind pivot pair (i<j). Tie-break toward the most
    recent: larger j, then larger i. Returns (i, j) indices into `pivots` or None."""
    best = None       # (amplitude, j, i)
    best_ij = None
    for i in range(len(pivots)):
        for j in range(i + 1, len(pivots)):
            if pivots[i][2] == pivots[j][2]:
                continue
            key = (abs(pivots[j][1] - pivots[i][1]), j, i)
            if best is None or key > best:
                best, best_ij = key, (i, j)
    return best_ij


def fibonacci_levels(df: pd.DataFrame, k: int = SWING_K,
                     lookback: int = LOOKBACK) -> dict:
    price = _last_close(df)
    pivots = _swing_points(df, k=k, lookback=lookback)
    highs = [p for p in pivots if p[2] == "high"]
    lows = [p for p in pivots if p[2] == "low"]
    if not highs or not lows or not np.isfinite(price):
        return {"available": False,
                "reason": "no confirmed swing (need both a swing high and a swing low)"}

    i, j = _dominant_pair(pivots)
    later = pivots[j]
    direction = "up" if later[2] == "high" else "down"
    hi = max(pivots[i], pivots[j], key=lambda p: p[1])
    lo = min(pivots[i], pivots[j], key=lambda p: p[1])
    high, low = hi[1], lo[1]
    diff = high - low
    win_len = min(lookback, len(df))

    def _pos(lvl):
        return "above" if lvl > price else "below"

    retr, ext = [], []
    for r in FIB_RETR:
        lvl = high - r * diff if direction == "up" else low + r * diff
        retr.append({"ratio": r, "price": round(lvl, 2), "pos": _pos(lvl)})
    for e in FIB_EXT:
        lvl = low + e * diff if direction == "up" else high - e * diff
        ext.append({"ratio": e, "price": round(lvl, 2), "pos": _pos(lvl)})

    all_lvls = retr + ext
    nearest = min(all_lvls, key=lambda d: abs(d["price"] - price))
    return {
        "swing": {
            "direction": direction,
            "high": round(high, 2), "high_date": str(hi[0].date()),
            "low": round(low, 2), "low_date": str(lo[0].date()),
            "amplitude_pct": round(100 * diff / low, 2) if low else None,
            "window_bars": int(win_len),
        },
        "retracements": retr,
        "extensions": ext,
        "nearest_level": {"ratio": nearest["ratio"], "price": nearest["price"],
                          "dist_pct": round(100 * (nearest["price"] - price) / price, 2)},
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_structure.py -q`
Expected: PASS (13 tests total).

- [ ] **Step 5: Commit**

```bash
git add structure.py tests/test_structure.py
git commit -m "feat(structure): dominant-swing Fibonacci retracement/extension levels"
```

---

### Task 4: Wire into `compute_indicators` + safety/window-honesty/integration tests

**Files:**
- Modify: `indicators.py` (import + two keys in `compute_indicators`)
- Test: `tests/test_structure.py`

**Interfaces:**
- Consumes: `support_resistance`, `fibonacci_levels` from Tasks 2–3; `indicators.compute_indicators`; `tools._clean`.
- Produces: `compute_indicators(df)` dict gains `"support_resistance"` and `"fibonacci"` keys.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_structure.py`:

```python
def test_window_honesty_reports_actual_bars(synth_ohlcv):
    df = synth_ohlcv(n=210)
    sr = structure.support_resistance(df)
    fib = structure.fibonacci_levels(df)
    assert "210 bars" in sr["method"]
    assert fib["swing"]["window_bars"] == 210


def test_safety_no_exceptions_and_json_clean(synth_ohlcv):
    # A short random series MAY legitimately have pivots -> "available"; the
    # invariant is only that we never throw and never leak a non-finite float.
    # A flat series has no swings -> must be unavailable.
    tiny = synth_ohlcv(n=8)
    flat = _frame([100.0] * 300)
    for fn in (structure.support_resistance, structure.fibonacci_levels):
        for df in (tiny, flat):
            out = fn(df)
            assert json.dumps(out, allow_nan=False)     # nothing non-finite leaked
        assert fn(flat)["available"] is False           # flat -> no confirmed swing


def test_compute_indicators_includes_structural_keys_and_is_json_clean(synth_ohlcv):
    import indicators as ind
    import tools
    df = synth_ohlcv(n=800)
    out = ind.compute_indicators(df)
    assert "support_resistance" in out
    assert "fibonacci" in out
    # tools._clean output must be strict-JSON serializable (no NaN/inf)
    json.dumps(tools._clean(out), allow_nan=False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_structure.py -q`
Expected: FAIL — `test_compute_indicators_includes_structural_keys_and_is_json_clean` fails on `assert "support_resistance" in out` (key not wired yet). `test_window_honesty_reports_actual_bars` and `test_safety_no_exceptions_and_json_clean` should already pass from Tasks 2–3; that's fine.

- [ ] **Step 3: Wire `indicators.py`**

Edit the import block near the top of `indicators.py` (after `from pandasta_data import load_asset`) to add:

```python
import structure
```

Edit `compute_indicators` (the `return {...}` at the end) to add the two keys after `"levels": _levels(df),`:

```python
    return {
        "overview": _overview(df),
        "trend": _trend(df),
        "momentum": _momentum(df),
        "volatility": _volatility(df),
        "volume": _volume(df),
        "levels": _levels(df),
        "support_resistance": structure.support_resistance(df),
        "fibonacci": structure.fibonacci_levels(df),
    }
```

- [ ] **Step 4: Run the full suite to verify pass + no regressions**

Run: `pytest -q`
Expected: PASS — new structural tests plus the existing suite (`test_indicators.py`, `test_tools.py`, etc.) all green.

- [ ] **Step 5: Manual smoke check on a real cached ticker**

Run: `python tools.py compute_indicators AAPL`
Expected: valid JSON printed; it contains `"support_resistance"` and `"fibonacci"` blocks with finite numbers (or `"available": false`), and no traceback.

- [ ] **Step 6: Commit**

```bash
git add indicators.py tests/test_structure.py
git commit -m "feat(indicators): expose support_resistance and fibonacci in compute_indicators"
```

---

### Task 5 (DEFERRED — do last, after Tasks 1–4 are verified): `prompt.py` wiring

Per the user's instruction, `prompt.py` is updated only once everything else is complete and verified. This task tells OpenClaw the new fields exist so it actually narrates them.

**Files:**
- Modify: `prompt.py`

**Interfaces:**
- Consumes: the `support_resistance` / `fibonacci` keys now present in `compute_indicators` output.
- Produces: no code interface — prompt text only.

- [ ] **Step 1: Locate where the prompt enumerates the `compute_indicators` fields**

Run: `grep -n "levels\|momentum\|volatility" prompt.py`
Expected: find the section of the prompt that lists the Layer-1 indicator blocks OpenClaw receives.

- [ ] **Step 2: Add two additive lines describing the new blocks**

In that same enumeration, add (matching the surrounding wording/format — adapt to the actual prose found in Step 1):

```
- `support_resistance`: nearest swing-pivot support/resistance zones (price, touch-count, recency). Layer-1 facts — describe them; do not invent levels not present here.
- `fibonacci`: dominant-swing retracement/extension levels with the anchoring swing. Layer-1 facts; if `available` is false, say no clean swing was found rather than guessing one.
```

- [ ] **Step 3: Verify the prompt still renders**

Run: `python -c "import prompt; print('ok')"` (and any existing prompt-render entry point, e.g. `pytest tests -q -k prompt` if present).
Expected: no import/render error; `ok` printed.

- [ ] **Step 4: Commit**

```bash
git add prompt.py
git commit -m "docs(prompt): tell OpenClaw about support_resistance and fibonacci blocks"
```

---

## Self-Review

**Spec coverage:**
- Swing detection + tie rule + causal confirmation → Task 1 (tests: single-peak, causal-confirmation, trailing-k, flat-top, flat-bottom). ✓
- Window honesty (`min(lookback,len)`, actual bars in `method`/`swing`) → implemented in Tasks 2–3, tested in Task 4 (`test_window_honesty_reports_actual_bars`). ✓
- ATR-relative S/R clustering + fixed-% fallback → Task 2 (`test_sr_atr_fallback_when_atr_nan`, widen/narrow via `cluster_atr` arg in cluster tests). ✓
- S/R split by price, `max_levels` cap, unavailable case → Task 2. ✓
- Fib dominant-swing (max-amplitude opposite pair, tie-break), no sparse fallback → Task 3 (`test_fib_dominant_swing_beats_recency_and_is_stable`, `test_fib_no_confirmed_swing_returns_unavailable`). ✓
- Fib retracement/extension math + nearest + pos → Task 3 (`test_fib_upswing_exact_math`). ✓
- Error handling / finite-guard / JSON-clean → Task 4 (`test_safety_short_and_flat_series`, `test_compute_indicators_includes_structural_keys_and_is_json_clean`). ✓
- Additive wiring, `_levels` kept, council untouched → Task 4 (keys appended; no council files modified). ✓
- `prompt.py` deferred → Task 5. ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete code. Task 5 Step 2 text adapts to the actual prose found in Step 1 (the file's current prompt wording isn't reproduced here), but the lines to add are given verbatim.

**Type consistency:** `_swing_points` returns `(Timestamp, float, str)` tuples; `_cluster` consumes `p[1]` (price) and `p[0]` (date); `_dominant_pair` consumes `pivots[i][1]`/`[2]`; `support_resistance`/`fibonacci_levels` return the dict shapes named in their Interfaces and asserted in the tests. `_atr`/`_last_close` names used consistently across tasks. ✓
