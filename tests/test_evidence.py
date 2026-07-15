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
