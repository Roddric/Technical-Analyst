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
        "available": True,
        "method": f"swing pivots k={k} over {win_len} bars, clustered within {tol_desc}",
        "supports": sup,
        "resistances": res,
        "nearest_support": sup[0]["price"] if sup else None,
        "nearest_resistance": res[0]["price"] if res else None,
    }
