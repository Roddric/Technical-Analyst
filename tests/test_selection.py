import numpy as np
import pandas as pd
import selection
import sets


def test_build_returns_sets_and_null(synth_ohlcv):
    df = synth_ohlcv(seed=8, drift=0.002)
    sig = selection.build_selected_sets(df)
    assert "Null" in sig
    set_names = [k for k in sig if k.startswith("Set")]
    assert len(set_names) >= 1
    for s in sig.values():
        assert len(s) == len(df) and s.notna().any()


def test_selection_is_deterministic(synth_ohlcv):
    df = synth_ohlcv(seed=8, drift=0.002)
    assert selection.select_roster(df) == selection.select_roster(df)


def test_selected_sets_are_error_decorrelated_on_train(synth_ohlcv):
    # The guarantee selection actually makes is decorrelation ON THE TRAIN SLICE
    # (by construction). Holdout decorrelation is NOT guaranteed and is reported,
    # not asserted -- train-decorrelation can be an in-sample artifact.
    df = synth_ohlcv(seed=8, drift=0.002)
    split = sets._train_slice(len(df))
    sig = selection.build_selected_sets(df)
    only_sets = {k: v.iloc[:split] for k, v in sig.items() if k.startswith("Set")}
    if len(only_sets) >= 2:
        rep = sets.check_error_decorrelation(only_sets, df.iloc[:split], mode="log",
                                             window=63, threshold=config_threshold())
        assert rep["max_abs_corr"] <= config_threshold() + 0.05


def config_threshold():
    import config
    return config.DECORR_THRESHOLD


def test_selection_is_walled_from_holdout(synth_ohlcv):
    # The roster must be chosen without seeing the holdout: corrupting holdout
    # bars (kept finite) must not change the selected membership.
    df = synth_ohlcv(seed=8, drift=0.002)
    n = len(df)
    split = sets._train_slice(n)
    roster_ref = selection.select_roster(df)

    corrupt = df.copy()
    rng = np.random.default_rng(999)
    factor = 1 + 0.5 * rng.standard_normal(n - split)
    for col in ("open", "high", "low", "close"):
        vals = corrupt[col].to_numpy("float64").copy()
        vals[split:] = np.abs(vals[split:] * factor) + 1.0   # different, still finite/positive
        corrupt[col] = vals
    roster_corrupt = selection.select_roster(corrupt)
    assert roster_ref == roster_corrupt
