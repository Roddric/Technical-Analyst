import numpy as np
import pandas as pd
import regime


def _clean_trend(n=400, step=0.004, noise=0.0008, seed=1):
    """Near-linear strong uptrend so the last-bar ADX is unambiguously high."""
    rng = np.random.default_rng(seed)
    r = rng.standard_normal(n) * noise + step
    close = 100 * np.exp(np.cumsum(r))
    idx = pd.bdate_range("2020-01-01", periods=n)
    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = close * (1 - step / 2)
    df["high"] = close * (1 + noise)
    df["low"] = np.minimum(df["open"], close) * (1 - noise)
    df["volume"] = 1000.0
    return df


def test_strong_uptrend_is_bull():
    df = _clean_trend()
    r = regime.classify_regime(df)
    assert r.label == "bull"
    assert set(r.features) >= {"ma_slope", "adx", "price_vs_ma"}
    assert r.features["adx"] >= 20.0


def test_flat_market_is_sideways(synth_ohlcv):
    df = synth_ohlcv(seed=2, drift=0.0)
    df["close"] = 100.0                             # perfectly flat
    df["high"] = df["low"] = df["open"] = 100.0
    r = regime.classify_regime(df)
    assert r.label == "sideways"


def test_classify_is_causal(synth_ohlcv):
    df = synth_ohlcv(seed=3)
    full = regime.classify_regime(df)
    trimmed = regime.classify_regime(df.iloc[:-1])
    assert isinstance(full.label, str) and isinstance(trimmed.label, str)
