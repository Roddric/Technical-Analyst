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
