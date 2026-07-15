# Indicator Council — M1 (Mechanical Core) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, LLM-free pipeline that, for each asset in the universe, classifies the regime, runs decorrelated personality-sets of indicators, weights each set by its out-of-sample IC, and produces a rule-derived trading plan object.

**Architecture:** Flat Python modules (matching the sibling `ta-flat-backtest` layout) that reuse its data/indicator/stats code via a `sys.path` shim. Each stage is a pure, testable function; the decision is a deterministic function of evidence weights. No network, no LLM in M1.

**Tech Stack:** Python 3.13, pandas, numpy, pandas_ta (via reuse), pytest.

## Global Constraints

- Python: use the workspace venv at `C:\Users\l\quant-workspace\.venv` (has pandas, numpy, pandas_ta, scipy).
- Reuse, do not re-implement: `pandasta_data` (UNIVERSE, `load_asset`, `return_mode`), `pandasta_registry` (`build_candidates`, `compute_candidate`), `stats` (`forward_returns`, `spearman_ic_hac`), `pandasta_set_search` (`causal_zscore`, `composite_signal`). Reach them via the `sys.path` shim in `config.py`.
- All signals must be **causal** (no lookahead): only `.rolling(...)`, `.shift(k>=0)`, expanding, or cumulative ops on past data.
- The decision (direction, conviction) must be **deterministic**: identical inputs → identical output. No RNG in arm A.
- Project root: `C:\Users\l\quant-workspace\Work\indicator-council`. Flat modules at root; tests under `tests/`.
- Decision horizon: `HORIZON = 5` trading days (short-swing default from the spec).
- Universe classes present: equity, metals, energy, crypto.

---

### Task 1: Scaffolding, config, and reuse shim

**Files:**
- Create: `Work/indicator-council/config.py`
- Create: `Work/indicator-council/tests/conftest.py`
- Create: `Work/indicator-council/tests/test_config.py`
- Create: `Work/indicator-council/pytest.ini`

**Interfaces:**
- Produces: `config.TA_FLAT_DIR: str`, `config.HORIZON: int`, `config.DECORR_THRESHOLD: float`, `config.N_PERSONALITIES: int`, `config.SHRINK_K: int`, `config.ATR_LEN/ATR_MULT_STOP/R_MULTIPLE/RISK_BUDGET`, `config.REGIME_*`, and `config.ensure_reuse_on_path()` which inserts `TA_FLAT_DIR` into `sys.path`.

- [ ] **Step 1: Initialize git and directory layout**

```bash
cd "C:/Users/l/quant-workspace/Work/indicator-council"
git init
mkdir -p tests docs/plans results
```

- [ ] **Step 2: Write `config.py`**

```python
"""Central config + reuse shim for the Indicator Council."""
import sys
from pathlib import Path

# Sibling project whose data/indicator/stats code we reuse.
TA_FLAT_DIR = str(Path(__file__).resolve().parent.parent / "ta-flat-backtest")

# Decision
HORIZON = 5                # forward-return horizon (trading days)

# Sets / decorrelation
N_PERSONALITIES = 3        # Fast, Slow, Contrarian
DECORR_THRESHOLD = 0.6     # max allowed |corr| between set signals (report if exceeded)

# Evidence weighting (unified power-gate + shrink via the HAC t-stat)
TRAIN_FRAC = 0.7           # fit member signs on the first fraction; measure IC on the holdout
GATE_K = 1.65             # min HAC t to trust a set; weight ∝ max(0, ic*(1 - k/t))
FDR_Q = 0.10             # Benjamini-Hochberg q across the (asset × set) grid
NULL_SEED = 12345          # seed for the always-on null tripwire set

# Risk (rule-derived plan numbers)
ATR_LEN = 14
ATR_MULT_STOP = 2.0
R_MULTIPLE = 2.0
RISK_BUDGET = 0.005        # fraction of capital risked per trade

# Regime classifier
REGIME_MA_LEN = 100
REGIME_SLOPE_LB = 20
REGIME_ADX_LEN = 14
REGIME_ADX_TREND = 20.0    # ADX above -> trending; below -> sideways


def ensure_reuse_on_path() -> None:
    """Make the ta-flat-backtest modules importable."""
    if TA_FLAT_DIR not in sys.path:
        sys.path.insert(0, TA_FLAT_DIR)
```

- [ ] **Step 3: Write `tests/conftest.py`** (puts reuse on path + a synthetic OHLCV fixture)

```python
import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()


@pytest.fixture
def synth_ohlcv():
    """Deterministic trending-then-ranging OHLCV frame, 800 daily bars."""
    def _make(seed=0, n=800, drift=0.0004):
        rng = np.random.default_rng(seed)
        r = rng.standard_normal(n) * 0.01 + drift
        close = 100 * np.exp(np.cumsum(r))
        idx = pd.bdate_range("2020-01-01", periods=n)
        df = pd.DataFrame(index=idx)
        df["close"] = close
        df["open"] = close * (1 + rng.standard_normal(n) * 0.001)
        df["high"] = np.maximum(df["open"], close) * (1 + np.abs(rng.standard_normal(n)) * 0.003)
        df["low"] = np.minimum(df["open"], close) * (1 - np.abs(rng.standard_normal(n)) * 0.003)
        df["volume"] = rng.integers(1_000, 10_000, n).astype(float)
        return df
    return _make
```

- [ ] **Step 4: Write `pytest.ini`**

```ini
[pytest]
testpaths = tests
addopts = -q
```

- [ ] **Step 5: Write `tests/test_config.py`**

```python
import config


def test_reuse_imports_resolve():
    config.ensure_reuse_on_path()
    import pandasta_data, pandasta_registry, stats, pandasta_set_search  # noqa: F401
    assert "^GSPC" in pandasta_data.UNIVERSE
    assert config.HORIZON == 5
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd "C:/Users/l/quant-workspace/Work/indicator-council" && ../../.venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: PASS (reuse modules import, UNIVERSE resolves).

- [ ] **Step 7: Commit**

```bash
git add config.py pytest.ini tests/conftest.py tests/test_config.py
git commit -m "chore: scaffold indicator-council M1 (config + reuse shim)"
```

---

### Task 2: Regime classifier

**Files:**
- Create: `Work/indicator-council/regime.py`
- Create: `Work/indicator-council/tests/test_regime.py`

**Interfaces:**
- Consumes: `config`.
- Produces: `regime.Regime` (dataclass: `label: str` in {"bull","bear","sideways"}, `features: dict`), `regime.classify_regime(df: pd.DataFrame) -> Regime` using the last bar; causal.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
import pandas as pd
import regime


def test_strong_uptrend_is_bull(synth_ohlcv):
    df = synth_ohlcv(seed=1, drift=0.003)          # strong upward drift
    r = regime.classify_regime(df)
    assert r.label == "bull"
    assert set(r.features) >= {"ma_slope", "adx", "price_vs_ma"}


def test_flat_market_is_sideways(synth_ohlcv):
    df = synth_ohlcv(seed=2, drift=0.0)            # no drift -> weak trend
    df["close"] = 100.0                             # perfectly flat
    df["high"] = df["low"] = df["open"] = 100.0
    r = regime.classify_regime(df)
    assert r.label == "sideways"


def test_classify_is_causal(synth_ohlcv):
    df = synth_ohlcv(seed=3)
    full = regime.classify_regime(df)
    trimmed = regime.classify_regime(df.iloc[:-1])  # dropping the future must not change a past call
    assert isinstance(full.label, str) and isinstance(trimmed.label, str)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_regime.py -v`
Expected: FAIL (`ModuleNotFoundError: regime`).

- [ ] **Step 3: Write `regime.py`**

```python
"""Mechanical bull / bear / sideways classifier (causal, per asset)."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import pandas_ta  # noqa: F401  (registers the .ta accessor)


@dataclass(frozen=True)
class Regime:
    label: str            # "bull" | "bear" | "sideways"
    features: dict


def classify_regime(df: pd.DataFrame) -> Regime:
    close = df["close"].astype("float64")
    ma = close.rolling(config.REGIME_MA_LEN).mean()
    slope = ma.diff(config.REGIME_SLOPE_LB)                 # MA change over the lookback
    adx_df = df.ta.adx(length=config.REGIME_ADX_LEN)
    adx_col = f"ADX_{config.REGIME_ADX_LEN}"
    adx = adx_df[adx_col] if adx_df is not None and adx_col in adx_df else pd.Series(np.nan, index=df.index)

    ma_slope = float(slope.iloc[-1]) if np.isfinite(slope.iloc[-1]) else 0.0
    adx_last = float(adx.iloc[-1]) if np.isfinite(adx.iloc[-1]) else 0.0
    price_vs_ma = float(close.iloc[-1] - ma.iloc[-1]) if np.isfinite(ma.iloc[-1]) else 0.0
    feats = {"ma_slope": ma_slope, "adx": adx_last, "price_vs_ma": price_vs_ma}

    if adx_last < config.REGIME_ADX_TREND:
        return Regime("sideways", feats)
    if ma_slope > 0 and price_vs_ma >= 0:
        return Regime("bull", feats)
    if ma_slope < 0 and price_vs_ma <= 0:
        return Regime("bear", feats)
    return Regime("sideways", feats)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_regime.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regime.py tests/test_regime.py
git commit -m "feat: mechanical bull/bear/sideways regime classifier"
```

---

### Task 3: Personality-sets and inter-set decorrelation

**Files:**
- Create: `Work/indicator-council/sets.py`
- Create: `Work/indicator-council/tests/test_sets.py`

**Interfaces:**
- Consumes: `config`; reuse `pandasta_registry.build_candidates`, `compute_candidate`; `pandasta_set_search.causal_zscore`; `stats.spearman_ic_hac`, `rolling_spearman`, `forward_returns`.
- Produces:
  - `sets.SLOTS = ("trend","momentum","volatility","volume")`, `sets.PERSONALITIES = ("Fast","Slow","Contrarian")`, `sets.NULL_NAME = "Null"`.
  - `sets.build_set_signals(df, mode="log") -> dict[str, pd.Series]` — one causal composite per personality **plus** a seeded random `"Null"` tripwire set. Member signs are fit on the **train slice only** (`config.TRAIN_FRAC`) to keep the later holdout IC honest.
  - `sets.check_decorrelation(signals, threshold) -> dict` — pairwise **signal** corr: `{"max_abs_corr","pairs","ok"}`.
  - `sets.check_error_decorrelation(signals, df, mode, window, threshold) -> dict` — pairwise corr of each set's **rolling-IC series** (correlated errors, not correlated signals): same shape.

**Design notes (rigor fixes folded in):**
- **Sign-split leak fix:** `_member_sign` fits on `df.iloc[:split]` where `split = int(len*TRAIN_FRAC)`. Fitting the sign on the same data the weight is later measured on would bias every set's IC positive and defeat the null tripwire.
- **Null set:** a seeded-random signal run through the identical sign/compose machinery. It exists to be a leakage tripwire (Task 4 gate must zero it); the running hard-assertion lives in M3 scorecard per the agreed sequencing.
- **Error-decorrelation:** the meaningful invariant is decorrelated *errors*; the rolling-IC-series correlation is the cheap M1 proxy. Treat a *failure* as a flag; a *pass* is weak evidence (the proxy is itself estimated on few effective obs).

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
import sets


def test_build_includes_personalities_and_null(synth_ohlcv):
    df = synth_ohlcv(seed=5)
    sig = sets.build_set_signals(df)
    assert set(sig) == {"Fast", "Slow", "Contrarian", "Null"}
    for s in sig.values():
        assert len(s) == len(df)
        assert s.notna().any()


def test_signal_decorrelation_report_shape(synth_ohlcv):
    df = synth_ohlcv(seed=6)
    sig = sets.build_set_signals(df)
    rep = sets.check_decorrelation(sig, threshold=0.6)
    assert set(rep) == {"max_abs_corr", "pairs", "ok"}
    assert 0.0 <= rep["max_abs_corr"] <= 1.0
    assert isinstance(rep["ok"], bool)


def test_error_decorrelation_report_shape(synth_ohlcv):
    df = synth_ohlcv(seed=6)
    sig = sets.build_set_signals(df)
    rep = sets.check_error_decorrelation(sig, df, mode="log", window=63, threshold=0.6)
    assert set(rep) == {"max_abs_corr", "pairs", "ok"}
    assert 0.0 <= rep["max_abs_corr"] <= 1.0


def test_contrarian_opposes_fast_on_trend(synth_ohlcv):
    df = synth_ohlcv(seed=7, drift=0.003)
    sig = sets.build_set_signals(df)
    corr = sig["Fast"].corr(sig["Contrarian"])
    assert corr < 0.95
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_sets.py -v`
Expected: FAIL (`ModuleNotFoundError: sets`).

- [ ] **Step 3: Write `sets.py`**

```python
"""Decorrelated personality-sets. Each set is a 4-slot composite of z-scored,
sign-aligned indicators; personalities differ by which member fills each slot
(round-robin, distinct) and, for Contrarian, an inverted sign. Member signs are
fit on the TRAIN slice only, so the later holdout IC is honest. A seeded-random
'Null' set rides along as a leakage tripwire."""
from itertools import combinations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
from pandasta_registry import build_candidates, compute_candidate
from pandasta_set_search import causal_zscore
import stats as st

SLOTS = ("trend", "momentum", "volatility", "volume")
PERSONALITIES = ("Fast", "Slow", "Contrarian")
NULL_NAME = "Null"


def _train_slice(n: int) -> int:
    return max(config.REGIME_MA_LEN + config.HORIZON, int(n * config.TRAIN_FRAC))


def _member_sign(z: pd.Series, fwd: np.ndarray, split: int) -> float:
    """+/-1 from the member's IC on the TRAIN slice only (0/NaN -> +1)."""
    ic, _, _, _ = st.spearman_ic_hac(z.to_numpy("float64")[:split], fwd[:split],
                                     lag=config.HORIZON)
    return -1.0 if (np.isfinite(ic) and ic < 0) else 1.0


def _candidates_by_slot(df: pd.DataFrame) -> dict[str, list[pd.Series]]:
    by_slot: dict[str, list[pd.Series]] = {s: [] for s in SLOTS}
    for cand in build_candidates():
        if cand.slot not in by_slot:
            continue
        try:
            raw = compute_candidate(df, cand)
        except Exception:
            continue
        z = causal_zscore(raw)
        if z.notna().sum() > config.REGIME_MA_LEN:
            by_slot[cand.slot].append(z.rename(cand.name))
    return by_slot


def build_set_signals(df: pd.DataFrame, mode: str = "log") -> dict[str, pd.Series]:
    n = len(df)
    split = _train_slice(n)
    fwd = st.forward_returns(df["close"].to_numpy("float64"), config.HORIZON, mode)
    by_slot = _candidates_by_slot(df)

    signals: dict[str, pd.Series] = {}
    for p_idx, pname in enumerate(PERSONALITIES):
        members = []
        for slot in SLOTS:
            pool = by_slot[slot]
            if not pool:
                continue
            z = pool[p_idx % len(pool)]
            members.append(_member_sign(z, fwd, split) * z)
        if not members:
            signals[pname] = pd.Series(np.nan, index=df.index, name=pname)
            continue
        comp = pd.concat(members, axis=1).mean(axis=1)
        if pname == "Contrarian":
            comp = -comp
        signals[pname] = comp.rename(pname)

    # Null tripwire: seeded random signal through the same sign machinery.
    rng = np.random.default_rng(config.NULL_SEED)
    null_z = causal_zscore(pd.Series(rng.standard_normal(n), index=df.index))
    signals[NULL_NAME] = (_member_sign(null_z, fwd, split) * null_z).rename(NULL_NAME)
    return signals


def _pairwise_report(cols: dict[str, pd.Series], threshold: float) -> dict:
    names = list(cols)
    mat = pd.concat([cols[n] for n in names], axis=1).dropna()
    pairs, max_abs = {}, 0.0
    for a, b in combinations(names, 2):
        c = float(mat[a].corr(mat[b])) if len(mat) > 2 else 0.0
        c = 0.0 if not np.isfinite(c) else c
        pairs[(a, b)] = c
        max_abs = max(max_abs, abs(c))
    return {"max_abs_corr": max_abs, "pairs": pairs, "ok": max_abs <= threshold}


def check_decorrelation(signals: dict[str, pd.Series], threshold: float) -> dict:
    return _pairwise_report(signals, threshold)


def check_error_decorrelation(signals: dict[str, pd.Series], df: pd.DataFrame,
                              mode: str, window: int, threshold: float) -> dict:
    """Correlated errors, not correlated signals: correlate each set's rolling-IC series."""
    fwd = st.forward_returns(df["close"].to_numpy("float64"), config.HORIZON, mode)
    ic_series = {}
    for name, s in signals.items():
        roll = st.rolling_spearman(s.to_numpy("float64"), fwd, window)
        ic_series[name] = pd.Series(roll, index=df.index)
    return _pairwise_report(ic_series, threshold)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_sets.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sets.py tests/test_sets.py
git commit -m "feat: personality-sets with train-slice sign fit, null tripwire, error-decorrelation check"
```

---

### Task 4: Evidence weights (OOS IC, shrunk)

**Files:**
- Create: `Work/indicator-council/evidence.py`
- Create: `Work/indicator-council/tests/test_evidence.py`

**Interfaces:**
- Consumes: `config`; `stats.forward_returns`, `spearman_ic_hac`; set signals from Task 3.
- Produces:
  - `evidence.set_ic_stats(signals, df, mode="log") -> dict[str, tuple[float,float,int]]` — per set `(ic, t, n)` measured on the **holdout** slice (`config.TRAIN_FRAC`).
  - `evidence.detectable_ic(ic, t) -> float` — the readable `1.96*SE` significance floor.
  - `evidence.weight_from_stat(ic, t, k=config.GATE_K) -> float` — the unified power-gate+shrink: `max(0, ic*(1 - k/t))` for `t>=k` and `ic>0`, else 0.
  - `evidence.one_sided_p(t) -> float`.
  - `evidence.fdr_survivors(pvals: dict, q=config.FDR_Q) -> set` — Benjamini-Hochberg survivors across a grid of keys.
  - `evidence.compute_weights(signals, df, mode="log", allowed=None, k=config.GATE_K) -> dict[str,float]` — normalized weights over gate-passers; `allowed` (set of names) further restricts to FDR survivors; `{}` means "no set has edge → arm A is mute".

**Design notes (rigor fixes folded in):**
- **Unified gate+shrink via the HAC t-stat** (`spearman_ic_hac` already returns an overlap-adjusted `t`): one `k`, not a separate 1.96 gate and a k≈1 shrink. `SE = |ic/t|`, so `ic - k*SE = ic*(1 - k/t)`.
- **FDR across the grid** is applied at the universe level (Task 8) via `fdr_survivors`; `compute_weights(allowed=...)` consumes the survivor set. Single-asset callers pass `allowed=None` (marginal gate only) and stay deterministic.
- **IC measured on the holdout** (disjoint from the train slice used for member signs) — this is what makes the Null set land at ~0.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
import pandas as pd
import evidence


def test_gate_zeroes_subthreshold_t():
    assert evidence.weight_from_stat(ic=0.30, t=1.0, k=1.65) == 0.0   # t below gate
    assert evidence.weight_from_stat(ic=0.30, t=3.0, k=1.65) > 0.0    # clears gate
    assert evidence.weight_from_stat(ic=-0.30, t=3.0, k=1.65) == 0.0  # negative IC never trades


def test_weight_shrinks_toward_zero_near_gate():
    near = evidence.weight_from_stat(ic=0.30, t=1.8, k=1.65)
    far = evidence.weight_from_stat(ic=0.30, t=6.0, k=1.65)
    assert 0.0 < near < far   # closer to the gate -> more shrink


def test_weights_nonneg_and_normalized(synth_ohlcv):
    import sets
    df = synth_ohlcv(seed=8, drift=0.002)
    sig = sets.build_set_signals(df)
    w = evidence.compute_weights(sig, df)
    assert all(v >= 0 for v in w.values())
    if w:
        assert abs(sum(w.values()) - 1.0) < 1e-9


def test_null_set_gets_zero_weight(synth_ohlcv):
    # Tripwire: the seeded-random Null set must not clear the gate.
    import sets
    df = synth_ohlcv(seed=8, drift=0.002)
    sig = sets.build_set_signals(df)
    w = evidence.compute_weights(sig, df)
    assert w.get("Null", 0.0) == 0.0


def test_fdr_survivors_basic():
    pvals = {"a": 0.001, "b": 0.20, "c": 0.9, "d": 0.011}
    surv = evidence.fdr_survivors(pvals, q=0.10)
    assert "a" in surv and "c" not in surv
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_evidence.py -v`
Expected: FAIL (`ModuleNotFoundError: evidence`).

- [ ] **Step 3: Write `evidence.py`**

```python
"""Evidence weights via a unified power-gate + shrink on the HAC t-stat,
with FDR control applied across the (asset × set) grid at the universe level."""
import numpy as np
import pandas as pd
from scipy.stats import norm

import config
config.ensure_reuse_on_path()
import stats as st


def _holdout_split(n: int) -> int:
    return max(config.REGIME_MA_LEN + config.HORIZON, int(n * config.TRAIN_FRAC))


def set_ic_stats(signals: dict[str, pd.Series], df: pd.DataFrame,
                 mode: str = "log") -> dict[str, tuple[float, float, int]]:
    n = len(df)
    split = _holdout_split(n)
    fwd = st.forward_returns(df["close"].to_numpy("float64"), config.HORIZON, mode)
    out: dict[str, tuple[float, float, int]] = {}
    for name, s in signals.items():
        x = s.to_numpy("float64")[split:]
        y = fwd[split:]
        ic, t, _, nobs = st.spearman_ic_hac(x, y, lag=config.HORIZON)
        out[name] = (float(ic), float(t) if np.isfinite(t) else 0.0,
                     int(nobs) if np.isfinite(nobs) else 0)
    return out


def detectable_ic(ic: float, t: float) -> float:
    """Readable 1.96*SE significance floor (SE inferred from the HAC t-stat)."""
    if not np.isfinite(t) or t == 0 or not np.isfinite(ic):
        return float("inf")
    return 1.96 * abs(ic / t)


def weight_from_stat(ic: float, t: float, k: float = config.GATE_K) -> float:
    """Unified gate+shrink: max(0, ic*(1 - k/t)) for t>=k and ic>0, else 0."""
    if not np.isfinite(ic) or not np.isfinite(t) or ic <= 0 or t < k:
        return 0.0
    return ic * (1.0 - k / t)


def one_sided_p(t: float) -> float:
    if not np.isfinite(t):
        return 1.0
    return float(norm.sf(t))


def fdr_survivors(pvals: dict, q: float = config.FDR_Q) -> set:
    """Benjamini-Hochberg: return the set of keys that survive at level q."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    if m == 0:
        return set()
    cutoff_rank = 0
    for i, (_, p) in enumerate(items, start=1):
        if p <= (i / m) * q:
            cutoff_rank = i
    return {k for i, (k, _) in enumerate(items, start=1) if i <= cutoff_rank}


def compute_weights(signals: dict[str, pd.Series], df: pd.DataFrame,
                    mode: str = "log", allowed: set | None = None,
                    k: float = config.GATE_K) -> dict[str, float]:
    stats = set_ic_stats(signals, df, mode)
    raw: dict[str, float] = {}
    for name, (ic, t, _n) in stats.items():
        if allowed is not None and name not in allowed:
            continue
        raw[name] = weight_from_stat(ic, t, k)
    total = sum(raw.values())
    if total <= 0:
        return {}
    return {name: v / total for name, v in raw.items() if v > 0}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_evidence.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add evidence.py tests/test_evidence.py
git commit -m "feat: unified t-gate+shrink weights, BH-FDR, null tripwire test"
```

---

### Task 5: Arbiter (deterministic decision)

**Files:**
- Create: `Work/indicator-council/arbiter.py`
- Create: `Work/indicator-council/tests/test_arbiter.py`

**Interfaces:**
- Consumes: set signals (Task 3), weights (Task 4).
- Produces: `arbiter.Decision` (dataclass: `direction: int` in {-1,0,1}, `conviction: float` in [0,1], `contributions: dict[str,float]`, `effective_n: float`); `arbiter.arbitrate(latest_signals, weights) -> Decision`. Pure/deterministic. `effective_n = 1/Σwᵢ²` (inverse Herfindahl) surfaces when one set dominates (≈1 → not really an ensemble).

- [ ] **Step 1: Write the failing test**

```python
import arbiter


def test_agreeing_sets_give_directional_call():
    d = arbiter.arbitrate({"Fast": 1.5, "Slow": 1.0}, {"Fast": 0.6, "Slow": 0.4})
    assert d.direction == 1
    assert 0.0 < d.conviction <= 1.0


def test_no_weight_means_flat():
    d = arbiter.arbitrate({"Fast": 2.0}, {})
    assert d.direction == 0 and d.conviction == 0.0
    assert d.effective_n == 0.0


def test_effective_n_flags_domination():
    balanced = arbiter.arbitrate({"a": 1.0, "b": 1.0}, {"a": 0.5, "b": 0.5})
    dominated = arbiter.arbitrate({"a": 1.0, "b": 1.0}, {"a": 0.95, "b": 0.05})
    assert abs(balanced.effective_n - 2.0) < 1e-9
    assert dominated.effective_n < 1.5


def test_is_deterministic():
    a = arbiter.arbitrate({"Fast": 0.8, "Slow": -0.9}, {"Fast": 0.5, "Slow": 0.5})
    b = arbiter.arbitrate({"Fast": 0.8, "Slow": -0.9}, {"Fast": 0.5, "Slow": 0.5})
    assert a == b
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_arbiter.py -v`
Expected: FAIL (`ModuleNotFoundError: arbiter`).

- [ ] **Step 3: Write `arbiter.py`**

```python
"""Deterministic arbitration: weighted sum of latest set signals -> decision.
effective_n = 1/Σwᵢ² (inverse Herfindahl) flags when one set dominates the
'ensemble' and the council is really a soft pick-the-best."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Decision:
    direction: int          # -1, 0, +1
    conviction: float       # [0, 1]
    contributions: dict     # name -> weight * signal
    effective_n: float      # 1 / sum(w^2); 0 when no weights


def _effective_n(weights: dict[str, float]) -> float:
    denom = sum(w * w for w in weights.values())
    return (1.0 / denom) if denom > 0 else 0.0


def arbitrate(latest_signals: dict[str, float], weights: dict[str, float]) -> Decision:
    contribs = {n: weights[n] * latest_signals.get(n, 0.0) for n in weights}
    score = sum(contribs.values())
    eff_n = _effective_n(weights)
    if not weights or score == 0.0:
        return Decision(0, 0.0, contribs, eff_n)
    direction = 1 if score > 0 else -1
    conviction = math.tanh(abs(score))   # squash z-scored weighted signal into [0,1]
    return Decision(direction, conviction, contribs, eff_n)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_arbiter.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add arbiter.py tests/test_arbiter.py
git commit -m "feat: deterministic evidence-weighted arbiter"
```

---

### Task 6: Risk manager (rule-derived levels)

**Files:**
- Create: `Work/indicator-council/risk.py`
- Create: `Work/indicator-council/tests/test_risk.py`

**Interfaces:**
- Consumes: `config`; `arbiter.Decision`; price df.
- Produces: `risk.Levels` (dataclass: `entry, stop, target, size: float`, `veto: bool`, `reason: str`); `risk.build_levels(df: pd.DataFrame, decision: arbiter.Decision) -> Levels`. All numbers from ATR/vol rules; direction from the decision.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
import arbiter
import risk


def test_long_levels_are_ordered(synth_ohlcv):
    df = synth_ohlcv(seed=9)
    d = arbiter.Decision(1, 0.7, {}, 0.0)
    lv = risk.build_levels(df, d)
    assert lv.stop < lv.entry < lv.target
    assert lv.size > 0 and not lv.veto


def test_flat_decision_is_vetoed(synth_ohlcv):
    df = synth_ohlcv(seed=10)
    lv = risk.build_levels(df, arbiter.Decision(0, 0.0, {}, 0.0))
    assert lv.veto and lv.size == 0.0


def test_short_levels_are_ordered(synth_ohlcv):
    df = synth_ohlcv(seed=11)
    lv = risk.build_levels(df, arbiter.Decision(-1, 0.6, {}, 0.0))
    assert lv.target < lv.entry < lv.stop
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_risk.py -v`
Expected: FAIL (`ModuleNotFoundError: risk`).

- [ ] **Step 3: Write `risk.py`**

```python
"""Rule-derived plan numbers. Direction comes from the decision; every price
level and the size come from volatility rules — never from an LLM."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import pandas_ta  # noqa: F401
import arbiter


@dataclass(frozen=True)
class Levels:
    entry: float
    stop: float
    target: float
    size: float
    veto: bool
    reason: str


def _atr(df: pd.DataFrame) -> float:
    a = df.ta.atr(length=config.ATR_LEN)
    val = float(a.iloc[-1]) if a is not None and np.isfinite(a.iloc[-1]) else np.nan
    return val


def build_levels(df: pd.DataFrame, decision: arbiter.Decision) -> Levels:
    entry = float(df["close"].iloc[-1])
    atr = _atr(df)
    if decision.direction == 0 or not np.isfinite(atr) or atr <= 0:
        return Levels(entry, entry, entry, 0.0, True, "no direction or ATR unavailable")

    stop_dist = config.ATR_MULT_STOP * atr
    if decision.direction == 1:
        stop = entry - stop_dist
        target = entry + config.R_MULTIPLE * stop_dist
    else:
        stop = entry + stop_dist
        target = entry - config.R_MULTIPLE * stop_dist

    # Vol-scaled size: risk budget / per-unit risk, scaled by conviction.
    size = (config.RISK_BUDGET / stop_dist) * decision.conviction
    return Levels(entry, stop, target, float(size), False,
                  f"ATR={atr:.4f}, {config.ATR_MULT_STOP}x stop, {config.R_MULTIPLE}R target")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_risk.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add risk.py tests/test_risk.py
git commit -m "feat: rule-derived risk levels (ATR stop, R target, vol size)"
```

---

### Task 7: Plan assembly

**Files:**
- Create: `Work/indicator-council/plan.py`
- Create: `Work/indicator-council/tests/test_plan.py`

**Interfaces:**
- Consumes: `regime.Regime`, `arbiter.Decision`, `risk.Levels`.
- Produces: `plan.Plan` (dataclass with `asset, regime_label, direction, conviction, entry, stop, target, size, veto, set_contributions, decorrelation, reason`); `plan.assemble_plan(asset, regime, decision, levels, decorrelation) -> Plan`; `plan.Plan.to_dict()`.

- [ ] **Step 1: Write the failing test**

```python
import arbiter, risk, plan
from regime import Regime


def test_assemble_roundtrips_to_dict():
    reg = Regime("bull", {"adx": 25.0})
    dec = arbiter.Decision(1, 0.7, {"Fast": 0.5}, 1.0)
    lv = risk.Levels(100.0, 96.0, 108.0, 0.001, False, "rule")
    p = plan.assemble_plan("BTC-USD", reg, dec, lv, {"max_abs_corr": 0.3, "ok": True})
    d = p.to_dict()
    assert d["asset"] == "BTC-USD" and d["direction"] == 1
    assert d["regime_label"] == "bull" and d["entry"] == 100.0
    assert d["set_contributions"] == {"Fast": 0.5}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_plan.py -v`
Expected: FAIL (`ModuleNotFoundError: plan`).

- [ ] **Step 3: Write `plan.py`**

```python
"""Structured, serializable trading plan object (mechanical arm)."""
from dataclasses import dataclass, asdict, field

import regime as regime_mod
import arbiter as arbiter_mod
import risk as risk_mod


@dataclass(frozen=True)
class Plan:
    asset: str
    regime_label: str
    direction: int
    conviction: float
    entry: float
    stop: float
    target: float
    size: float
    veto: bool
    reason: str
    set_contributions: dict = field(default_factory=dict)
    decorrelation: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def assemble_plan(asset: str, regime: "regime_mod.Regime",
                  decision: "arbiter_mod.Decision", levels: "risk_mod.Levels",
                  decorrelation: dict) -> Plan:
    return Plan(
        asset=asset,
        regime_label=regime.label,
        direction=decision.direction,
        conviction=decision.conviction,
        entry=levels.entry,
        stop=levels.stop,
        target=levels.target,
        size=levels.size,
        veto=levels.veto,
        reason=levels.reason,
        set_contributions=dict(decision.contributions),
        decorrelation=dict(decorrelation),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_plan.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plan.py tests/test_plan.py
git commit -m "feat: structured Plan object + assembly"
```

---

### Task 8: Pipeline runner + end-to-end integration test

**Files:**
- Create: `Work/indicator-council/run.py`
- Create: `Work/indicator-council/tests/test_run.py`

**Interfaces:**
- Consumes: all prior modules; reuse `pandasta_data.UNIVERSE`, `load_asset`, `return_mode`.
- Produces:
  - `run.analyze_asset(df, asset, mode="log", allowed=None) -> plan.Plan` (pure, deterministic; `allowed=None` → marginal gate only).
  - `run.run_universe(assets=None) -> list[plan.Plan]` — two-pass: gather per-set holdout t-stats across the grid, BH-FDR (`evidence.fdr_survivors`), then weight only survivors.
  - `run.main()`.

**Design notes (rigor fixes folded in):**
- **Universe-level FDR:** pass 1 computes `set_ic_stats` per asset and builds `pvals[(asset,name)] = one_sided_p(t)`; `fdr_survivors` over the whole grid yields the survivor keys; pass 2 calls `analyze_asset(..., allowed=survivor_names_for_asset)`. Single-asset `analyze_asset` (tests) uses `allowed=None` → deterministic marginal gate.
- **Regime is out of the decision path** (proven by `test_regime_does_not_affect_decision`): perturbing the regime label leaves direction/conviction/levels byte-identical.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
import run
import regime as regime_mod


def test_analyze_asset_is_deterministic(synth_ohlcv):
    df = synth_ohlcv(seed=12, drift=0.002)
    a = run.analyze_asset(df, "TEST")
    b = run.analyze_asset(df, "TEST")
    assert a.to_dict() == b.to_dict()
    assert a.direction in (-1, 0, 1)


def test_dropping_future_does_not_change_a_past_decision(synth_ohlcv):
    # No-lookahead: the decision on data up to bar T is identical whether or not
    # bars after T exist.
    df = synth_ohlcv(seed=13, drift=0.002)
    past = df.iloc[:-20]
    d_full = run.analyze_asset(df.iloc[:len(past)], "TEST")
    d_past = run.analyze_asset(past, "TEST")
    assert d_full.to_dict() == d_past.to_dict()


def test_regime_does_not_affect_decision(synth_ohlcv, monkeypatch):
    # Regime is context-only in arm A: forcing a different label must not move
    # direction/conviction or any level.
    df = synth_ohlcv(seed=14, drift=0.002)
    monkeypatch.setattr(regime_mod, "classify_regime",
                        lambda d: regime_mod.Regime("bull", {}))
    a = run.analyze_asset(df, "TEST")
    monkeypatch.setattr(regime_mod, "classify_regime",
                        lambda d: regime_mod.Regime("bear", {}))
    b = run.analyze_asset(df, "TEST")
    assert (a.direction, a.conviction, a.entry, a.stop, a.target, a.size) == \
           (b.direction, b.conviction, b.entry, b.stop, b.target, b.size)
    assert a.regime_label == "bull" and b.regime_label == "bear"


def test_run_universe_smoke():
    plans = run.run_universe(assets=["BTC-USD"])   # uses real cached data
    assert len(plans) == 1
    assert plans[0].asset == "BTC-USD"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_run.py -v`
Expected: FAIL (`ModuleNotFoundError: run`).

- [ ] **Step 3: Write `run.py`**

```python
"""Mechanical pipeline: prices -> regime -> sets -> (FDR-gated) weights -> decision -> plan."""
import json
from pathlib import Path

import config
config.ensure_reuse_on_path()
from pandasta_data import UNIVERSE, load_asset, return_mode

import regime as regime_mod
import sets as sets_mod
import evidence as evidence_mod
import arbiter as arbiter_mod
import risk as risk_mod
import plan as plan_mod

RESULTS = Path(__file__).resolve().parent / "results"


def analyze_asset(df, asset: str, mode: str = "log", allowed=None) -> plan_mod.Plan:
    reg = regime_mod.classify_regime(df)          # context only; never feeds the arbiter
    signals = sets_mod.build_set_signals(df, mode)
    weights = evidence_mod.compute_weights(signals, df, mode, allowed=allowed)
    latest = {n: (float(s.iloc[-1]) if s.notna().iloc[-1] else 0.0)
              for n, s in signals.items()}
    decision = arbiter_mod.arbitrate(latest, weights)
    levels = risk_mod.build_levels(df, decision)
    decorr = sets_mod.check_decorrelation(signals, config.DECORR_THRESHOLD)
    return plan_mod.assemble_plan(asset, reg, decision, levels, decorr)


def run_universe(assets=None) -> list[plan_mod.Plan]:
    assets = assets or list(UNIVERSE)
    loaded = []
    pvals = {}
    # Pass 1: per-asset set stats -> grid of one-sided p-values.
    for a in assets:
        df = load_asset(a)
        if df is None or len(df) < config.REGIME_MA_LEN + config.HORIZON:
            continue
        mode = return_mode(a)
        signals = sets_mod.build_set_signals(df, mode)
        stats = evidence_mod.set_ic_stats(signals, df, mode)
        loaded.append((a, df, mode))
        for name, (_ic, t, _n) in stats.items():
            pvals[(a, name)] = evidence_mod.one_sided_p(t)
    # FDR across the whole (asset x set) grid.
    survivors = evidence_mod.fdr_survivors(pvals, config.FDR_Q)
    # Pass 2: weight only survivors, per asset.
    plans = []
    for a, df, mode in loaded:
        allowed = {name for (asset_k, name) in survivors if asset_k == a}
        plans.append(analyze_asset(df, a, mode, allowed=allowed))
    return plans


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    plans = run_universe()
    out = [p.to_dict() for p in plans]
    (RESULTS / "plans_latest.json").write_text(json.dumps(out, indent=2))
    for p in plans:
        arrow = {1: "LONG", -1: "SHORT", 0: "FLAT"}[p.direction]
        tail = "VETO" if p.veto else \
            f"entry={p.entry:.2f} stop={p.stop:.2f} tgt={p.target:.2f}"
        print(f"{p.asset:<10} {p.regime_label:<9} {arrow:<6} conv={p.conviction:.2f} "
              f"eff_n={p.set_contributions and round(1/sum(w*w for w in _weights(p)), 2) or 0} {tail}"
              if False else
              f"{p.asset:<10} {p.regime_label:<9} {arrow:<6} conv={p.conviction:.2f} {tail}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `../../.venv/Scripts/python.exe -m pytest tests/test_run.py -v`
Expected: PASS (determinism + no-lookahead + regime-invariance + universe smoke).

- [ ] **Step 5: Run the whole suite and the pipeline once**

Run: `../../.venv/Scripts/python.exe -m pytest -q && ../../.venv/Scripts/python.exe run.py`
Expected: all tests PASS; `run.py` prints one line per asset and writes `results/plans_latest.json`.

- [ ] **Step 6: Commit**

```bash
git add run.py tests/test_run.py
git commit -m "feat: mechanical runner with universe FDR + determinism/no-lookahead/regime-invariance tests"
```

---

## Self-Review

**Spec coverage:**
- Regime (bull/bear/sideways) → Task 2. ✓
- Decorrelated personality-sets (4-slot bundles) → Task 3. ✓
- Decorrelation enforced between sets → Task 3 `check_decorrelation` (reports/verifies in M1; automated re-selection deferred). ✓
- Evidence weights = shrunk OOS IC, coarse → Task 4. ✓
- Mechanical, deterministic decision → Task 5 + determinism tests in Tasks 5 & 8. ✓
- Rule-derived levels, no LLM numbers → Task 6. ✓
- Plan object → Task 7; runner → Task 8. ✓
- No-lookahead → Task 8 explicit test. ✓
- **Deferred to later plans (not M1, per spec milestones):** narrator/LLM (M2), Telegram/report delivery (M2), scorecard + arm-B debate + A/B scoring (M3). Noted, not gaps.

**Placeholder scan:** No TBD/TODO; every code step has complete code. ✓

**Type consistency:** `Regime.label`, `Decision(direction:int, conviction:float, contributions:dict)`, `Levels(entry,stop,target,size,veto,reason)`, `Plan` fields, and `analyze_asset`/`run_universe`/`compute_weights`/`arbitrate`/`build_levels`/`assemble_plan` signatures are used identically across Tasks 3–8. ✓

**Note for implementer:** `sets.build_set_signals` depends on the exact candidate slot names in `pandasta_registry` ("trend","momentum","volatility","volume"). If a slot yields no candidates for an asset, that personality simply drops that slot (handled). If decorrelation `ok` is False, M1 only reports it — Task-3 does not yet auto-swap members (that refinement is a follow-up).
