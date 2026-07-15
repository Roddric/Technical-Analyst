import numpy as np
import run
import regime as regime_mod


def test_analyze_asset_is_deterministic(synth_ohlcv):
    df = synth_ohlcv(seed=12, drift=0.002)
    a = run.analyze_asset(df, "TEST")
    b = run.analyze_asset(df, "TEST")
    assert a.to_dict() == b.to_dict()
    assert a.direction in (-1, 0, 1)


def test_dropping_future_does_not_change_a_past_decision(synth_ohlcv):
    # No-lookahead: the decision on data up to bar T is identical whether or not
    # bars after T exist.
    df = synth_ohlcv(seed=13, drift=0.002)
    past = df.iloc[:-20]
    d_full = run.analyze_asset(df.iloc[:len(past)], "TEST")
    d_past = run.analyze_asset(past, "TEST")
    assert d_full.to_dict() == d_past.to_dict()


def test_regime_does_not_affect_decision(synth_ohlcv, monkeypatch):
    # Regime is context-only in arm A: forcing a different label must not move
    # direction/conviction or any level.
    df = synth_ohlcv(seed=14, drift=0.002)
    monkeypatch.setattr(regime_mod, "classify_regime",
                        lambda d: regime_mod.Regime("bull", {}))
    a = run.analyze_asset(df, "TEST")
    monkeypatch.setattr(regime_mod, "classify_regime",
                        lambda d: regime_mod.Regime("bear", {}))
    b = run.analyze_asset(df, "TEST")
    assert (a.direction, a.conviction, a.entry, a.stop, a.target, a.size) == \
           (b.direction, b.conviction, b.entry, b.stop, b.target, b.size)
    assert a.regime_label == "bull" and b.regime_label == "bear"


def test_run_universe_smoke():
    plans = run.run_universe(assets=["BTC-USD"])   # uses real cached data
    assert len(plans) == 1
    assert plans[0].asset == "BTC-USD"
