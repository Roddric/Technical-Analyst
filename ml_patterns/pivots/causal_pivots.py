"""Step 0 — causal (confirmation-lagged) pivot detection.

Pivot detection is INHERENTLY NON-CAUSAL. Calling a bar a local maximum requires
seeing the bars after it: at time t you cannot know whether t is the peak until
enough later bars have failed to exceed it. `scipy.signal.argrelextrema` and
every naive `rolling(...).max()` centred window has this property.

That leak sits UPSTREAM of any window-level lookahead guard. If pivots are found
on the full series and features are then windowed, a guard on the window sees a
perfectly well-formed window and passes — while the pivot inside it encodes the
future. Every IC computed downstream would be fake, and it would fail silently
by looking good.

The fix is a confirmation lag. A pivot at bar `t` is only KNOWN at bar `t + k`,
once k subsequent bars have failed to exceed it. Features may only read pivots
whose confirmation bar has already passed.

Nothing downstream may import `_raw_pivots`. Use `confirmed_pivots` or
`pivot_state`, both of which are causal by construction.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PIVOT_HIGH = "high"
PIVOT_LOW = "low"


def _raw_pivots(high: np.ndarray, low: np.ndarray, k: int) -> list[tuple[int, str, float]]:
    """NON-CAUSAL. Internal only — never call this from feature code.

    Bar t is a pivot high iff high[t] is a STRICT maximum of the centred window
    [t-k, t+k]. Strictness makes plateaus produce no pivot, which is the
    conservative choice: an ambiguous flat top is not a pivot rather than an
    arbitrarily-chosen one. Returns (index, kind, price), index-ascending.
    """
    n = len(high)
    out: list[tuple[int, str, float]] = []
    if k < 1 or n == 0:
        return out
    for t in range(k, n - k):
        lo, hi = t - k, t + k + 1
        win_h = high[lo:hi]
        if np.isfinite(high[t]) and np.isfinite(win_h).all():
            # strict max: equal to the window max, and uniquely so
            if high[t] == win_h.max() and (win_h == high[t]).sum() == 1:
                out.append((t, PIVOT_HIGH, float(high[t])))
        win_l = low[lo:hi]
        if np.isfinite(low[t]) and np.isfinite(win_l).all():
            if low[t] == win_l.min() and (win_l == low[t]).sum() == 1:
                out.append((t, PIVOT_LOW, float(low[t])))
    out.sort(key=lambda r: r[0])
    return out


def confirmed_pivots(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Causal pivot table. One row per pivot, with the bar at which it becomes
    KNOWN (`confirm_pos = pos + k`).

    A pivot whose confirmation bar falls beyond the end of the frame is DROPPED,
    not reported early: at the right edge of the series there are genuinely
    unconfirmed candidates, and emitting them is exactly the leak this module
    exists to prevent. That means the last k bars never contribute pivots — a
    real cost, and the correct one.

    Columns: pos, time, kind, price, confirm_pos, confirm_time.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["pos", "time", "kind", "price",
                                     "confirm_pos", "confirm_time"])
    high = df["high"].to_numpy("float64")
    low = df["low"].to_numpy("float64")
    n = len(df)
    rows = []
    for pos, kind, price in _raw_pivots(high, low, k):
        confirm_pos = pos + k
        if confirm_pos >= n:            # not yet knowable inside this frame
            continue
        rows.append({"pos": pos, "time": df.index[pos], "kind": kind,
                     "price": price, "confirm_pos": confirm_pos,
                     "confirm_time": df.index[confirm_pos]})
    return pd.DataFrame(rows, columns=["pos", "time", "kind", "price",
                                       "confirm_pos", "confirm_time"])


def pivot_state(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Per-bar causal pivot state — the feature-facing surface.

    For every bar T, reports the most recent CONFIRMED pivot high and low as of
    T, and how many bars ago each occurred. A pivot found at bar t only appears
    from bar t+k onward, so reading this frame at T can never encode anything
    after T.

    Columns (all NaN until the first confirmation):
        last_high_price, last_high_age, last_low_price, last_low_age
    `age` is measured from the pivot bar itself (t), not its confirmation bar,
    so it is a true "bars since the extreme" — it simply is not readable until
    the extreme is confirmed.
    """
    idx = df.index if df is not None else pd.Index([])
    cols = ["last_high_price", "last_high_age", "last_low_price", "last_low_age"]
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=cols, index=idx, dtype=float)

    n = len(df)
    piv = confirmed_pivots(df, k)
    hp = np.full(n, np.nan)      # price of last confirmed pivot high
    hpos = np.full(n, np.nan)    # bar position of that pivot
    lp = np.full(n, np.nan)
    lpos = np.full(n, np.nan)

    # Place each pivot's information AT its confirmation bar, then forward-fill.
    for r in piv.itertuples(index=False):
        c = int(r.confirm_pos)
        if r.kind == PIVOT_HIGH:
            hp[c], hpos[c] = r.price, r.pos
        else:
            lp[c], lpos[c] = r.price, r.pos

    out = pd.DataFrame({"last_high_price": hp, "_hpos": hpos,
                        "last_low_price": lp, "_lpos": lpos}, index=idx).ffill()
    pos = np.arange(n, dtype="float64")
    out["last_high_age"] = pos - out["_hpos"]
    out["last_low_age"] = pos - out["_lpos"]
    return out[cols]
