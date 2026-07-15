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
