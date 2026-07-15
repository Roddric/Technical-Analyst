import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()


@pytest.fixture
def synth_ohlcv():
    """Deterministic trending-then-ranging OHLCV frame, 800 daily bars."""
    def _make(seed=0, n=800, drift=0.0004):
        rng = np.random.default_rng(seed)
        r = rng.standard_normal(n) * 0.01 + drift
        close = 100 * np.exp(np.cumsum(r))
        idx = pd.bdate_range("2020-01-01", periods=n)
        df = pd.DataFrame(index=idx)
        df["close"] = close
        df["open"] = close * (1 + rng.standard_normal(n) * 0.001)
        df["high"] = np.maximum(df["open"], close) * (1 + np.abs(rng.standard_normal(n)) * 0.003)
        df["low"] = np.minimum(df["open"], close) * (1 - np.abs(rng.standard_normal(n)) * 0.003)
        df["volume"] = rng.integers(1_000, 10_000, n).astype(float)
        return df
    return _make
