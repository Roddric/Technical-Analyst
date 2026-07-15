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
    if decision.direction == 0:
        return Levels(entry, entry, entry, 0.0, True, "no set cleared the evidence gate")
    if not np.isfinite(atr) or atr <= 0 or entry <= 0:
        return Levels(entry, entry, entry, 0.0, True, "ATR unavailable")

    stop_dist = config.ATR_MULT_STOP * atr
    if decision.direction == 1:
        stop = entry - stop_dist
        target = entry + config.R_MULTIPLE * stop_dist
    else:
        stop = entry + stop_dist
        target = entry - config.R_MULTIPLE * stop_dist

    # Notional fraction of capital sized so a stop-out loses ~RISK_BUDGET of
    # capital, scaled by conviction and capped at 1x (no leverage in the report).
    frac_stop = stop_dist / entry
    size = min(1.0, (config.RISK_BUDGET / frac_stop) * decision.conviction)
    return Levels(entry, stop, target, float(size), False,
                  f"ATR={atr:.4f}, {config.ATR_MULT_STOP}x stop, {config.R_MULTIPLE}R target, "
                  f"size risks {config.RISK_BUDGET:.1%} at stop")
