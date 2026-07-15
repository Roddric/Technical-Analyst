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
