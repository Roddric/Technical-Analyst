"""Deterministic arbitration: weighted sum of latest set signals -> decision.
effective_n = 1/sum(w^2) (inverse Herfindahl) flags when one set dominates the
'ensemble' and the council is really a soft pick-the-best."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Decision:
    direction: int          # -1, 0, +1
    conviction: float       # [0, 1]
    contributions: dict     # name -> weight * signal
    effective_n: float      # 1 / sum(w^2); 0 when no weights
    long_only_suppressed: bool = False   # True iff a short was forced flat by long-only


def _effective_n(weights: dict[str, float]) -> float:
    denom = sum(w * w for w in weights.values())
    return (1.0 / denom) if denom > 0 else 0.0


def arbitrate(latest_signals: dict[str, float], weights: dict[str, float],
              long_only: bool = False) -> Decision:
    contribs = {n: weights[n] * latest_signals.get(n, 0.0) for n in weights}
    score = sum(contribs.values())
    eff_n = _effective_n(weights)
    if not weights or score == 0.0:
        return Decision(0, 0.0, contribs, eff_n)
    if score < 0 and long_only:
        # Bearish signal, but the long-only mandate takes no short position. Report
        # flat, but keep the evidence (contribs / effective_n) and flag WHY it is
        # flat so downstream can tell a suppressed short from a genuine no-signal.
        return Decision(0, 0.0, contribs, eff_n, long_only_suppressed=True)
    direction = 1 if score > 0 else -1
    conviction = math.tanh(abs(score))   # squash z-scored weighted signal into [0,1]
    return Decision(direction, conviction, contribs, eff_n)
