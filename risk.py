"""Rule-derived plan numbers. Direction comes from the decision; every price
level and the size come from volatility rules -- never from an LLM."""
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
    return float(a.iloc[-1]) if a is not None and np.isfinite(a.iloc[-1]) else np.nan


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

    size = (config.RISK_BUDGET / stop_dist) * decision.conviction
    return Levels(entry, stop, target, float(size), False,
                  f"ATR={atr:.4f}, {config.ATR_MULT_STOP}x stop, {config.R_MULTIPLE}R target")
