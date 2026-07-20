"""Step 2 — geometric features from CONFIRMED pivots only.

Every feature here is built from `causal_pivots.confirmed_pivots`, which reports
a pivot only once its confirmation bar has passed. Nothing in this module may
import `_raw_pivots`: that function is non-causal, and using it would leak
upstream of any window-level guard (see pivots/causal_pivots.py).

`compute_indicators(df) -> dict[str, pd.Series]` is a HARD interface, not a
convenience. `vendor/stats.surrogate_ic_ir_null` consumes exactly that signature
to build the null distribution in Step 4 — it rebuilds surrogate OHLCV paths and
recomputes every feature from them. Changing this signature breaks the null
control, which is the one thing standing between a real edge and a plausible
number.

Feature design note: these describe swing STRUCTURE (are highs rising? is the
range compressing? where does price sit in the channel?), not named chart
patterns. That is deliberate — see the module naming discussion in
labeling/geometric_forward_return.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()

from ml_patterns.pivots.causal_pivots import (
    confirmed_pivots, PIVOT_HIGH, PIVOT_LOW,
)

DEFAULT_K = 5


def _recent_confirmed(df: pd.DataFrame, k: int, n_each: int = 2) -> dict[str, np.ndarray]:
    """For every bar T, the last `n_each` confirmed highs and lows as of T.

    Causal by construction: a pivot enters the running state at its confirmation
    bar, so bar T can only ever see pivots confirmed at or before T.

    Returns arrays shaped (len(df),) per slot, e.g. high_price_0 is the most
    recent confirmed high, high_price_1 the one before it.
    """
    n = len(df)
    piv = confirmed_pivots(df, k)
    out: dict[str, np.ndarray] = {}
    for kind, tag in ((PIVOT_HIGH, "high"), (PIVOT_LOW, "low")):
        for j in range(n_each):
            out[f"{tag}_price_{j}"] = np.full(n, np.nan)
            out[f"{tag}_pos_{j}"] = np.full(n, np.nan)

    by_confirm: dict[int, list] = {}
    for r in piv.itertuples(index=False):
        by_confirm.setdefault(int(r.confirm_pos), []).append(r)

    hist = {PIVOT_HIGH: [], PIVOT_LOW: []}      # most-recent-first
    for t in range(n):
        for r in by_confirm.get(t, []):
            hist[r.kind].insert(0, (r.pos, r.price))
            del hist[r.kind][n_each:]
        for kind, tag in ((PIVOT_HIGH, "high"), (PIVOT_LOW, "low")):
            for j in range(n_each):
                if j < len(hist[kind]):
                    pos_j, price_j = hist[kind][j]
                    out[f"{tag}_price_{j}"][t] = price_j
                    out[f"{tag}_pos_{j}"][t] = pos_j
    return out


def _safe_div(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.asarray(a, dtype="float64") / np.asarray(b, dtype="float64")
    return np.where(np.isfinite(r), r, np.nan)


def compute_indicators(df: pd.DataFrame, k: int = DEFAULT_K) -> dict[str, pd.Series]:
    """The Step-2 feature surface, and the interface Step 4's null control needs.

    All features are scale-free (ratios or normalised distances) so they are
    comparable across assets and across the surrogate paths the null control
    generates — a raw price level would make the null incomparable to the real
    series.

    Returns dict[name -> Series] aligned to df.index. NaN until the relevant
    pivots are confirmed; downstream must not fill those.
    """
    idx = df.index if df is not None else pd.Index([])
    if df is None or len(df) == 0:
        return {}

    close = df["close"].to_numpy("float64")
    p = _recent_confirmed(df, k, n_each=2)
    pos = np.arange(len(df), dtype="float64")

    h0, h1 = p["high_price_0"], p["high_price_1"]
    l0, l1 = p["low_price_0"], p["low_price_1"]
    hp0, hp1 = p["high_pos_0"], p["high_pos_1"]
    lp0, lp1 = p["low_pos_0"], p["low_pos_1"]

    span = h0 - l0                                  # current confirmed channel

    feats: dict[str, np.ndarray] = {
        # where price sits relative to the confirmed swing structure
        "gfr_px_vs_high": _safe_div(close, h0) - 1.0,
        "gfr_px_vs_low": _safe_div(close, l0) - 1.0,
        "gfr_channel_pos": _safe_div(close - l0, span),      # 0 at low, 1 at high
        "gfr_channel_width": _safe_div(span, close),         # amplitude, scale-free

        # structure: are highs rising and lows rising? (trend) — scale-free
        "gfr_high_step": _safe_div(h0 - h1, np.abs(h1)),
        "gfr_low_step": _safe_div(l0 - l1, np.abs(l1)),

        # compression / expansion: successive channel widths (triangles, wedges)
        "gfr_span_ratio": _safe_div(h0 - l0, h1 - l1),

        # timing / symmetry — how stale is the structure, how evenly spaced
        "gfr_high_age": pos - hp0,
        "gfr_low_age": pos - lp0,
        "gfr_leg_symmetry": _safe_div(np.abs(hp0 - lp0), np.abs(hp1 - lp1)),
    }

    # volume confirmation: today's volume against its own trailing median, which
    # is causal (rolling, past-only) and scale-free.
    if "volume" in df:
        vol = df["volume"].astype("float64")
        med = vol.rolling(20).median()
        feats["gfr_volume_confirm"] = _safe_div(vol.to_numpy(), med.to_numpy())

    return {name: pd.Series(v, index=idx, name=name) for name, v in feats.items()}


FEATURE_NAMES = (
    "gfr_px_vs_high", "gfr_px_vs_low", "gfr_channel_pos", "gfr_channel_width",
    "gfr_high_step", "gfr_low_step", "gfr_span_ratio", "gfr_high_age",
    "gfr_low_age", "gfr_leg_symmetry", "gfr_volume_confirm",
)
