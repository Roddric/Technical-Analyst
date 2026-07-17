# Cross-Market Linkage — Phase A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two causally-aligned cross-listing signals for SK Hynix — ADR overnight transmission and ADR premium reversion — into the `000660.KS` council, plus a live descriptive premium snapshot for OpenClaw.

**Architecture:** One new module `cross_market.py` owns all cross-listing logic as pure, fixture-testable functions: a causal as-of alignment primitive, a causal z-score, the two signals, and a snapshot. It plugs into `run.analyze_asset` by appending its signals to the existing signal dict (so they flow through `evidence.py` → `arbiter` and are OOS-gated like everything else), and into `tools.compute_indicators` for the descriptive snapshot. No arbiter/risk/plan changes.

**Tech Stack:** Python 3, pandas, numpy, pytest. Loader is `pandasta_data.load_asset`.

**Spec:** `docs/superpowers/specs/2026-07-17-cross-market-linkage-design.md` (Phase A only; Phase B / 07709 is a separate later plan).

## Global Constraints

- **Causal alignment is the load-bearing invariant.** Every foreign leg is attached to the target bar with an as-of *backward* merge; for Phase A the foreign date must be **strictly before** the target date (`allow_exact_matches=False`) — a US print dated D must never enter the D bar.
- **Pure + fixture-testable.** All signal logic operates on passed-in DataFrames, never fetches inside the math. `load_asset` is called only at the orchestrator edge (`build_signals`) and is injectable for tests.
- **Graceful degradation.** Missing/short/failed foreign data → the signal is simply absent (`build_signals` returns `{}` or omits a key) or `{"available": false, ...}` for the snapshot. Never a crash, never a fabricated value; nothing non-finite propagates.
- **Honest gating.** The two signals earn weight only through the existing `evidence.compute_weights` OOS machinery. This plan adds signals; it does not change how they're weighted.
- **Single-asset path.** `000660.KS` is used via `analyze_ticker` (on-demand), where `analyze_asset` runs with `allowed=None` (marginal t-gate). Batch-FDR integration is out of scope — `000660.KS` is not in the 14-asset batch universe.
- **Fixed constants (from spec):** `XMKT_Z_WINDOW=60`, `XMKT_MIN_HISTORY=150`, `CROSS_MARKET_MAP={"000660.KS": {"adr":"US.SKHY","fx":"KRW=X","adr_ratio":1.0}}`, snapshot band `±3%`.
- **Run tests from repo root** with `pytest` (`pythonpath=.`, `addopts=-q`).

## File Structure

- **Create** `cross_market.py` — sole owner of cross-listing signal logic.
- **Create** `tests/test_cross_market.py` — all unit tests for the module.
- **Modify** `config.py` — add `XMKT_Z_WINDOW`, `XMKT_MIN_HISTORY`, `CROSS_MARKET_MAP`.
- **Modify** `run.py` — import `cross_market`, append its signals in `analyze_asset`.
- **Modify** `tools.py` — add the descriptive `cross_market` snapshot block to `compute_indicators` for configured tickers.

---

### Task 1: `cross_market.py` scaffold + causal primitives

**Files:**
- Create: `cross_market.py`
- Modify: `config.py`
- Test: `tests/test_cross_market.py`

**Interfaces:**
- Consumes: `config` constants.
- Produces:
  - `_asof_align(target_index: pd.DatetimeIndex, foreign: pd.DataFrame, strict_before: bool = True) -> pd.DataFrame` — `foreign` columns reindexed to `target_index` by as-of backward merge.
  - `_causal_zscore(s: pd.Series, window: int = 60) -> pd.Series` — trailing-window z-score, non-finite → NaN.

- [ ] **Step 1: Add config constants**

In `config.py`, after the `HORIZON`/`LONG_ONLY` lines in the `# Decision` block, add:

```python
# Cross-market linkage (Phase A: SK Hynix ADR)
XMKT_Z_WINDOW = 60          # trailing window for causal z-scores
XMKT_MIN_HISTORY = 150      # aligned finite bars required before a signal is emitted
CROSS_MARKET_MAP = {        # target ticker -> foreign legs
    "000660.KS": {"adr": "US.SKHY", "fx": "KRW=X", "adr_ratio": 1.0},
}
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_cross_market.py`:

```python
import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

import cross_market


def _frame(dates, closes):
    """OHLCV frame with flat OHLC = close, on the given dates."""
    closes = np.asarray(closes, dtype=float)
    idx = pd.to_datetime(list(dates))
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes,
         "volume": np.ones(len(closes))},
        index=idx,
    )


def test_asof_strict_before_excludes_same_date():
    foreign = _frame(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
                     [10, 20, 30, 40])
    target = pd.to_datetime(["2021-01-02", "2021-01-03", "2021-01-04"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=True)
    # each target date maps to the PRIOR foreign date, never the same date
    assert list(aligned["close"].values) == [10.0, 20.0, 30.0]


def test_asof_allow_exact_uses_same_date():
    foreign = _frame(["2021-01-01", "2021-01-02", "2021-01-03"], [10, 20, 30])
    target = pd.to_datetime(["2021-01-02", "2021-01-03"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=False)
    assert list(aligned["close"].values) == [20.0, 30.0]


def test_asof_holiday_robust_and_no_future_leak():
    # foreign missing 2021-01-02; target 2021-01-03 falls back to 01-01
    foreign = _frame(["2021-01-01", "2021-01-04"], [10, 40])
    target = pd.to_datetime(["2021-01-03"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=True)
    assert aligned["close"].iloc[0] == 10.0            # last before D, not the future 40


def test_causal_zscore_is_causal_and_correct():
    s = pd.Series(np.arange(1, 21, dtype=float))
    full = cross_market._causal_zscore(s, window=5)
    partial = cross_market._causal_zscore(s.iloc[:10], window=5)
    assert full.iloc[9] == pytest.approx(partial.iloc[9])   # future bars don't move it
    # manual check at index 9: window = values 6..10, mean 8, std(ddof=1)=1.5811, z=(10-8)/1.5811
    assert full.iloc[9] == pytest.approx((10 - 8) / np.std([6, 7, 8, 9, 10], ddof=1))


def test_causal_zscore_flat_series_is_nan_not_inf():
    s = pd.Series([5.0] * 10)
    z = cross_market._causal_zscore(s, window=5)
    assert not np.isinf(z).any()
    assert z.iloc[-1] != z.iloc[-1] or np.isnan(z.iloc[-1])   # NaN, not inf
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_cross_market.py -q`
Expected: FAIL / ERROR — `AttributeError: module 'cross_market' has no attribute '_asof_align'`.

- [ ] **Step 4: Write `cross_market.py` with the primitives**

Create `cross_market.py`:

```python
"""Cross-market (cross-listing) signals for SK Hynix — Phase A.

Treats 000660.KS (Korea, the anchor) and US.SKHY (the US ADR, same underlying)
as one asset in two venues. Produces two causally-aligned mechanical signals
(overnight transmission, premium reversion) plus a live premium snapshot.

CAUSAL: every foreign leg is attached with an as-of BACKWARD merge; for the
Korea target the foreign date must be strictly before the target date, because a
US close dated D only prints ~06:00 KST on D+1 (after KRX closes on D)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
from pandasta_data import load_asset

XMKT_Z_WINDOW = config.XMKT_Z_WINDOW
XMKT_MIN_HISTORY = config.XMKT_MIN_HISTORY


def _asof_align(target_index: pd.DatetimeIndex, foreign: pd.DataFrame,
                strict_before: bool = True) -> pd.DataFrame:
    """Reindex `foreign` onto `target_index` by as-of backward merge.
    strict_before=True -> foreign date must be < target date (no same-date match)."""
    cols = list(foreign.columns)
    target_index = pd.DatetimeIndex(target_index)
    if foreign is None or len(foreign) == 0:
        return pd.DataFrame(index=target_index, columns=cols, dtype=float)
    left = pd.DataFrame({"_t": target_index}).sort_values("_t")
    right = foreign.sort_index().reset_index()
    right.columns = ["_f"] + cols
    merged = pd.merge_asof(left, right, left_on="_t", right_on="_f",
                           direction="backward", allow_exact_matches=not strict_before)
    merged.index = pd.DatetimeIndex(merged["_t"])
    return merged[cols].reindex(target_index)


def _causal_zscore(s: pd.Series, window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Trailing-window z-score using only data up to each point; non-finite -> NaN."""
    mean = s.rolling(window).mean()
    std = s.rolling(window).std()
    z = (s - mean) / std
    return z.replace([np.inf, -np.inf], np.nan)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_cross_market.py -q`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add cross_market.py config.py tests/test_cross_market.py
git commit -m "feat(cross_market): causal as-of alignment + causal z-score primitives"
```

---

### Task 2: ADR overnight transmission signal

**Files:**
- Modify: `cross_market.py`
- Test: `tests/test_cross_market.py`

**Interfaces:**
- Consumes: `_asof_align`, `_causal_zscore` from Task 1.
- Produces: `adr_overnight_signal(target_df: pd.DataFrame, adr_df: pd.DataFrame, window: int = 60) -> pd.Series` named `"xmkt_adr_overnight"`, indexed to `target_df.index`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cross_market.py`:

```python
def test_adr_overnight_uses_prior_foreign_return_and_is_causal():
    # ADR closes; its daily returns are aligned to the PRIOR foreign date for each target
    adr = _frame(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
                 [100, 110, 121, 121])                 # returns: nan, +0.10, +0.10, 0.0
    target = _frame(["2021-01-03", "2021-01-04", "2021-01-05"], [1, 1, 1])
    sig = cross_market.adr_overnight_signal(target, adr, window=2)
    assert sig.name == "xmkt_adr_overnight"
    assert list(sig.index) == list(target.index)
    # target 2021-01-03 sees ADR return as-of < 01-03 -> the 01-02 return (+0.10)
    raw = cross_market._asof_align(target.index, adr["close"].pct_change().to_frame("r"),
                                   strict_before=True)["r"]
    assert raw.iloc[0] == pytest.approx(0.10)


def test_adr_overnight_never_leaks_same_or_future_day():
    adr = _frame(["2021-01-01", "2021-01-02", "2021-01-03"], [100, 200, 400])
    target = _frame(["2021-01-02"], [1])
    raw = cross_market._asof_align(target.index, adr["close"].pct_change().to_frame("r"),
                                   strict_before=True)["r"]
    # at target 01-02, the only usable ADR return is 01-01's (which is NaN, first bar) -
    # crucially NOT the 01-02 (+1.0) or 01-03 (+1.0) returns
    assert raw.iloc[0] != pytest.approx(1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cross_market.py -q`
Expected: FAIL — `AttributeError: module 'cross_market' has no attribute 'adr_overnight_signal'`.

- [ ] **Step 3: Implement the signal**

Append to `cross_market.py`:

```python
def adr_overnight_signal(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                         window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Transmission: the ADR's freshest daily return available before the Korea
    bar (as-of, strictly before), causal-z-scored. Sign/weight learned OOS."""
    adr_ret = adr_df["close"].pct_change().to_frame("adr_ret")
    aligned = _asof_align(target_df.index, adr_ret, strict_before=True)["adr_ret"]
    return _causal_zscore(aligned, window).rename("xmkt_adr_overnight")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cross_market.py -q`
Expected: PASS (7 tests total).

- [ ] **Step 5: Commit**

```bash
git add cross_market.py tests/test_cross_market.py
git commit -m "feat(cross_market): ADR overnight transmission signal"
```

---

### Task 3: ADR premium signal + live snapshot

**Files:**
- Modify: `cross_market.py`
- Test: `tests/test_cross_market.py`

**Interfaces:**
- Consumes: `_asof_align`, `_causal_zscore`.
- Produces:
  - `adr_premium_signal(target_df, adr_df, fx_df, adr_ratio: float = 1.0, window: int = 60) -> pd.Series` named `"xmkt_adr_premium"`.
  - `adr_premium_snapshot(target_df, adr_df, fx_df, adr_ratio: float = 1.0, band: float = 0.03) -> dict` — either `{"available": False, "reason": ...}` or keys `adr_price, fx, adr_ratio, adr_in_krw, local_price, premium_pct, band_pct, zone`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cross_market.py`:

```python
def test_adr_premium_snapshot_matches_hand_calc():
    # 152.31 * 1480 = 225418.8 ; / 228500 - 1 = -1.349% -> -1.35
    target = _frame(["2026-07-15", "2026-07-16"], [228500, 228500])
    adr = _frame(["2026-07-14", "2026-07-15"], [150.0, 152.31])
    fx = _frame(["2026-07-14", "2026-07-15"], [1480.0, 1480.0])
    snap = cross_market.adr_premium_snapshot(target, adr, fx, adr_ratio=1.0)
    assert snap["available"] is True
    assert snap["premium_pct"] == pytest.approx(-1.35, abs=0.01)
    assert snap["zone"] == "within_band"


def test_adr_premium_snapshot_zone_bands():
    target = _frame(["2026-01-01"], [100.0])
    adr_rich = _frame(["2026-01-01"], [110.0])          # +10% -> rich
    fx = _frame(["2026-01-01"], [1.0])
    assert cross_market.adr_premium_snapshot(target, adr_rich, fx, 1.0)["zone"] == "rich"
    adr_cheap = _frame(["2026-01-01"], [90.0])           # -10% -> cheap
    assert cross_market.adr_premium_snapshot(target, adr_cheap, fx, 1.0)["zone"] == "cheap"


def test_adr_premium_snapshot_missing_data_unavailable():
    target = _frame(["2026-01-01"], [100.0])
    empty = _frame([], [])
    snap = cross_market.adr_premium_snapshot(target, empty, empty, 1.0)
    assert snap["available"] is False


def test_adr_premium_signal_is_series_aligned_to_target():
    n = 80
    dates = pd.bdate_range("2021-01-01", periods=n)
    target = _frame(dates, np.linspace(200000, 230000, n))
    adr = _frame(dates, np.linspace(140, 155, n))
    fx = _frame(dates, np.full(n, 1480.0))
    sig = cross_market.adr_premium_signal(target, adr, fx, adr_ratio=1.0, window=20)
    assert sig.name == "xmkt_adr_premium"
    assert list(sig.index) == list(target.index)
    assert np.isfinite(sig.iloc[-1])           # enough history -> finite tail
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cross_market.py -q`
Expected: FAIL — `AttributeError: ... 'adr_premium_signal'`.

- [ ] **Step 3: Implement premium signal + snapshot**

Append to `cross_market.py`:

```python
def _last_finite(df: pd.DataFrame) -> float:
    if df is None or "close" not in df or len(df) == 0:
        return float("nan")
    c = df["close"].dropna()
    return float(c.iloc[-1]) if len(c) else float("nan")


def adr_premium_signal(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                       fx_df: pd.DataFrame, adr_ratio: float = 1.0,
                       window: int = XMKT_Z_WINDOW) -> pd.Series:
    """Premium reversion: (ADR-in-KRW / local) - 1, on causally-aligned foreign
    legs, causal-z-scored. Same underlying so the fair ratio is 1 (no beta fit)."""
    adr_close = _asof_align(target_df.index, adr_df[["close"]], strict_before=True)["close"]
    fx = _asof_align(target_df.index, fx_df[["close"]], strict_before=True)["close"]
    adr_krw = adr_close * fx * adr_ratio
    premium = adr_krw / target_df["close"] - 1.0
    return _causal_zscore(premium, window).rename("xmkt_adr_premium")


def adr_premium_snapshot(target_df: pd.DataFrame, adr_df: pd.DataFrame,
                         fx_df: pd.DataFrame, adr_ratio: float = 1.0,
                         band: float = 0.03) -> dict:
    """Live descriptive premium from the latest available print of each venue."""
    adr, fx, local = _last_finite(adr_df), _last_finite(fx_df), _last_finite(target_df)
    if not np.isfinite([adr, fx, local]).all() or local == 0:
        return {"available": False, "reason": "missing ADR / FX / local price"}
    adr_krw = adr * fx * adr_ratio
    premium = adr_krw / local - 1.0
    zone = "rich" if premium > band else "cheap" if premium < -band else "within_band"
    return {"available": True, "adr_price": round(adr, 4), "fx": round(fx, 4),
            "adr_ratio": adr_ratio, "adr_in_krw": round(adr_krw, 2),
            "local_price": round(local, 2), "premium_pct": round(100 * premium, 2),
            "band_pct": round(100 * band, 2), "zone": zone}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cross_market.py -q`
Expected: PASS (11 tests total).

- [ ] **Step 5: Commit**

```bash
git add cross_market.py tests/test_cross_market.py
git commit -m "feat(cross_market): ADR premium reversion signal + live snapshot"
```

---

### Task 4: `build_signals` orchestrator + graceful degradation

**Files:**
- Modify: `cross_market.py`
- Test: `tests/test_cross_market.py`

**Interfaces:**
- Consumes: `adr_overnight_signal`, `adr_premium_signal`, `config.CROSS_MARKET_MAP`, `load_asset`.
- Produces: `build_signals(target_df: pd.DataFrame, asset: str, loader=load_asset) -> dict[str, pd.Series]` — `{}` if the asset isn't configured or data is missing/short; otherwise the subset of `{"xmkt_adr_overnight", "xmkt_adr_premium"}` that has ≥ `XMKT_MIN_HISTORY` finite bars.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cross_market.py`:

```python
def _long_legs(n=300):
    dates = pd.bdate_range("2020-01-01", periods=n)
    target = _frame(dates, np.linspace(200000, 230000, n))
    adr = _frame(dates, np.linspace(140, 155, n))
    fx = _frame(dates, np.full(n, 1480.0))
    return target, adr, fx


def test_build_signals_returns_both_with_fake_loader():
    target, adr, fx = _long_legs()
    loader = lambda t: {"US.SKHY": adr, "KRW=X": fx}.get(t)
    sigs = cross_market.build_signals(target, "000660.KS", loader=loader)
    assert set(sigs) == {"xmkt_adr_overnight", "xmkt_adr_premium"}
    assert all(len(s) == len(target) for s in sigs.values())


def test_build_signals_unconfigured_asset_is_empty():
    target, _, _ = _long_legs()
    assert cross_market.build_signals(target, "AAPL", loader=lambda t: None) == {}


def test_build_signals_missing_leg_is_empty():
    target, _, _ = _long_legs()
    assert cross_market.build_signals(target, "000660.KS", loader=lambda t: None) == {}


def test_build_signals_short_history_is_empty():
    target, adr, fx = _long_legs(n=50)          # < XMKT_MIN_HISTORY
    loader = lambda t: {"US.SKHY": adr, "KRW=X": fx}.get(t)
    assert cross_market.build_signals(target, "000660.KS", loader=loader) == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cross_market.py -q`
Expected: FAIL — `AttributeError: ... 'build_signals'`.

- [ ] **Step 3: Implement the orchestrator**

Append to `cross_market.py`:

```python
def build_signals(target_df: pd.DataFrame, asset: str, loader=load_asset) -> dict:
    """Load the configured foreign legs and return the cross-market signal series
    for `asset`. Returns {} if unconfigured or data is missing/too short."""
    cfg = config.CROSS_MARKET_MAP.get(asset)
    if not cfg:
        return {}
    adr_df, fx_df = loader(cfg["adr"]), loader(cfg["fx"])
    if adr_df is None or adr_df.empty or fx_df is None or fx_df.empty:
        return {}
    ratio = cfg.get("adr_ratio", 1.0)
    candidates = {
        "xmkt_adr_overnight": adr_overnight_signal(target_df, adr_df),
        "xmkt_adr_premium": adr_premium_signal(target_df, adr_df, fx_df, ratio),
    }
    return {name: s for name, s in candidates.items()
            if s.notna().sum() >= XMKT_MIN_HISTORY}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cross_market.py -q`
Expected: PASS (15 tests total).

- [ ] **Step 5: Commit**

```bash
git add cross_market.py tests/test_cross_market.py
git commit -m "feat(cross_market): build_signals orchestrator with graceful degradation"
```

---

### Task 5: Wire into `run.analyze_asset`

**Files:**
- Modify: `run.py`
- Test: `tests/test_cross_market.py`

**Interfaces:**
- Consumes: `cross_market.build_signals`.
- Produces: `analyze_asset` appends cross-market signals to the signal dict before weighting, for any asset in `CROSS_MARKET_MAP`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_cross_market.py` (self-contained; uses the shared `synth_ohlcv` fixture from `tests/conftest.py`):

```python
def test_run_analyze_asset_appends_cross_market_signals(monkeypatch, synth_ohlcv):
    import run
    df = synth_ohlcv(n=300, seed=3)
    seen = {}

    def fake_build(target_df, asset, loader=None):
        seen["asset"] = asset
        seen["is_df"] = target_df is df
        return {}                       # empty -> no behavior change, just verify wiring

    monkeypatch.setattr(run.cross_market_mod, "build_signals", fake_build)
    run.analyze_asset(df, "000660.KS")
    assert seen["asset"] == "000660.KS" and seen["is_df"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cross_market.py::test_run_analyze_asset_appends_cross_market_signals -q`
Expected: FAIL — `AttributeError: module 'run' has no attribute 'cross_market_mod'`.

- [ ] **Step 3: Wire `run.py`**

Add the import after line `import report as report_mod`:

```python
import cross_market as cross_market_mod
```

In `analyze_asset`, immediately after the `signals = selection_mod.build_selected_sets(...)` line, add:

```python
    signals.update(cross_market_mod.build_signals(df, asset))
```

- [ ] **Step 4: Run the full suite**

Run: `pytest -q`
Expected: PASS — the new wiring test plus the entire existing suite (no regressions).

- [ ] **Step 5: Manual smoke check (live data, degrades gracefully)**

Run: `python -c "import run; p = run.analyze_ticker('000660.KS'); print(None if p is None else (p.direction, list(p.set_contributions)[:8]))"`
Expected: either a Plan prints (and if US.SKHY/KRW=X are fetchable with ≥150 aligned bars, `xmkt_adr_overnight`/`xmkt_adr_premium` may appear among contributions), or `None` / a plan with no `xmkt_` keys if the foreign data isn't available — **no traceback** either way. Record which occurred (this is the live-data prerequisite check from the spec).

- [ ] **Step 6: Commit**

```bash
git add run.py tests/test_cross_market.py
git commit -m "feat(run): append cross-market signals for configured assets"
```

---

### Task 6: Descriptive premium snapshot in `compute_indicators`

**Files:**
- Modify: `tools.py`
- Test: `tests/test_cross_market.py`

**Interfaces:**
- Consumes: `cross_market.adr_premium_snapshot`, `config.CROSS_MARKET_MAP`, `indicators.get_stock_data`.
- Produces: `compute_indicators(ticker)` output gains a `"cross_market"` key for tickers in `CROSS_MARKET_MAP` (the snapshot dict, or `{"available": false, ...}`).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_cross_market.py`:

```python
def test_compute_indicators_adds_cross_market_snapshot(monkeypatch):
    import json
    import tools
    import cross_market as cm

    target, adr, fx = _long_legs()
    # make the descriptive fetch return our synthetic legs, and the local df
    monkeypatch.setattr(tools.ind, "get_stock_data",
                        lambda t, *a, **k: {"US.SKHY": adr, "KRW=X": fx,
                                            "000660.KS": target}.get(t))
    # keep the indicator suite itself from doing heavy work: stub compute_indicators core
    monkeypatch.setattr(tools.ind, "compute_indicators", lambda df: {"overview": {}})
    monkeypatch.setattr(tools, "council_verdict", lambda t: {"available": False})
    monkeypatch.setattr(tools.tradelog, "record_plan", lambda *a, **k: False)

    out = tools.compute_indicators("000660.KS")
    assert "cross_market" in out
    assert out["cross_market"]["available"] is True
    json.dumps(tools._clean(out), allow_nan=False)          # strict-JSON clean
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cross_market.py::test_compute_indicators_adds_cross_market_snapshot -q`
Expected: FAIL — `assert "cross_market" in out` fails (not wired yet).

- [ ] **Step 3: Wire `tools.py`**

At the top of `tools.py`, add an import next to the existing `import indicators as ind`:

```python
import cross_market
```

In `compute_indicators(ticker)`, after the line `out["council"] = council_verdict(ticker)` and before the `tradelog.record_plan` line, add:

```python
    cfg = config.CROSS_MARKET_MAP.get(ticker)
    if cfg:
        adr = ind.get_stock_data(cfg["adr"])
        fx = ind.get_stock_data(cfg["fx"])
        local = ind.get_stock_data(ticker)
        if adr is not None and fx is not None and local is not None:
            out["cross_market"] = cross_market.adr_premium_snapshot(
                local, adr, fx, cfg.get("adr_ratio", 1.0))
        else:
            out["cross_market"] = {"available": False, "reason": "foreign data unavailable"}
```

- [ ] **Step 4: Run the full suite**

Run: `pytest -q`
Expected: PASS — the snapshot test plus the whole suite green.

- [ ] **Step 5: Commit**

```bash
git add tools.py tests/test_cross_market.py
git commit -m "feat(tools): expose cross-market ADR premium snapshot in compute_indicators"
```

---

## Self-Review

**Spec coverage (Phase A):**
- Causal as-of alignment (strict-before) → Task 1 (`_asof_align` + 3 alignment tests). ✓
- ADR overnight transmission → Task 2. ✓
- ADR premium reversion (direct ratio, FX + adr_ratio, β≡1) → Task 3 (`adr_premium_signal`; hand-calc −1.35% test). ✓
- Live descriptive snapshot + ±3% bands → Task 3 (`adr_premium_snapshot`). ✓
- OOS-gated integration via existing `evidence` → Task 5 (append to signal dict; weighting unchanged). ✓
- Graceful degradation / no non-finite / no crash → Tasks 3–4 (unavailable snapshot, `{}` orchestrator) + Task 6 JSON-clean. ✓
- Live-data prerequisite check → Task 5 Step 5 smoke (records whether the foreign tickers fetch). ✓
- Phase B (07709), ADR-liquidity study, batch-FDR integration → explicitly out of scope (separate plan / noted constraints). ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete code. Task 5's test is self-contained on the shared `synth_ohlcv` fixture.

**Type consistency:** `_asof_align` returns a DataFrame (callers index `["close"]`/`["adr_ret"]`); signals are `pd.Series` named `xmkt_adr_overnight` / `xmkt_adr_premium` consistently across Tasks 2–5; `build_signals(target_df, asset, loader=...)` matches the `run.py` call `build_signals(df, asset)` (loader defaulted); `adr_premium_snapshot(...)` dict keys match between Task 3 and the Task 6 JSON-clean test. `run.cross_market_mod` alias used consistently in Task 5 test and wiring. ✓
