import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

import price_cache


def test_fetch_yf_normalizes_multiindex_and_tz(monkeypatch):
    # yfinance often returns MultiIndex (field, ticker) columns + tz-aware index.
    idx = pd.date_range("2026-07-10", periods=3, tz="America/New_York")
    raw = pd.DataFrame(
        {("Open", "SKHY"): [1.0, 2.0, 3.0], ("High", "SKHY"): [1.0, 2.0, 3.0],
         ("Low", "SKHY"): [1.0, 2.0, 3.0], ("Close", "SKHY"): [10.0, 20.0, 30.0],
         ("Volume", "SKHY"): [100, 200, 300]},
        index=idx,
    )
    raw.columns = pd.MultiIndex.from_tuples(raw.columns)
    monkeypatch.setattr("yfinance.download", lambda *a, **k: raw)

    out = price_cache._fetch_yf("SKHY")
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
    assert out.index.name == "Date"
    assert out.index.tz is None                       # tz stripped to naive
    assert float(out["close"].iloc[-1]) == 30.0


def test_fetch_yf_fills_missing_volume_for_fx(monkeypatch):
    # FX series (e.g. KRW=X) have no Volume column — must not crash, volume -> NaN.
    idx = pd.date_range("2026-07-10", periods=2)
    raw = pd.DataFrame({"Open": [1480.0, 1481.0], "High": [1485.0, 1486.0],
                        "Low": [1478.0, 1479.0], "Close": [1480.5, 1481.5]}, index=idx)
    monkeypatch.setattr("yfinance.download", lambda *a, **k: raw)

    out = price_cache._fetch_yf("KRW=X")
    assert "volume" in out.columns
    assert out["volume"].isna().all()
    assert float(out["close"].iloc[-1]) == 1481.5


def test_fetch_yf_empty_returns_none(monkeypatch):
    monkeypatch.setattr("yfinance.download", lambda *a, **k: pd.DataFrame())
    assert price_cache._fetch_yf("NOPE") is None
