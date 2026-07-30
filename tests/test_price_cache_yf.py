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


def test_fetch_yf_falls_back_when_max_period_returns_empty(monkeypatch):
    """Yahoo returns an EMPTY frame (not an error) for some live symbols on
    period='max' — e.g. 7203.T. Without a bounded-window retry a tradeable
    symbol looks delisted, which downstream cannot distinguish from 'no data'."""
    idx = pd.date_range("2026-07-10", periods=2)
    good = pd.DataFrame({"Open": [1.0, 2.0], "High": [1.0, 2.0], "Low": [1.0, 2.0],
                         "Close": [10.0, 20.0], "Volume": [1, 2]}, index=idx)
    seen = []

    def fake_download(tkr, period=None, **k):
        seen.append(period)
        return pd.DataFrame() if period == "max" else good

    monkeypatch.setattr("yfinance.download", fake_download)
    out = price_cache._fetch_yf("7203.T")
    assert seen == ["max", "10y"]                    # tried max first, then fell back
    assert out is not None and float(out["close"].iloc[-1]) == 20.0


def test_fetch_yf_empty_on_both_attempts_returns_none(monkeypatch):
    monkeypatch.setattr("yfinance.download", lambda *a, **k: pd.DataFrame())
    assert price_cache._fetch_yf("DELISTED") is None


def _normalized_frame(start="2026-07-10", periods=3):
    idx = pd.date_range(start, periods=periods, name="Date")
    return pd.DataFrame({
        "open": np.arange(periods) + 10.0,
        "high": np.arange(periods) + 11.0,
        "low": np.arange(periods) + 9.0,
        "close": np.arange(periods) + 10.5,
        "volume": np.arange(periods) + 100.0,
    }, index=idx)


def test_refresh_atomically_advances_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(price_cache, "CACHE_DIR", str(tmp_path))
    old = _normalized_frame(periods=2)
    old.to_csv(price_cache._path("CRCL"))
    fresh = _normalized_frame(periods=4)
    monkeypatch.setattr(price_cache, "_fetch", lambda ticker: fresh)

    out = price_cache.refresh("CRCL")

    assert out.equals(fresh)
    cached = price_cache.load("CRCL")
    assert len(cached) == 4
    assert cached.index[-1] == fresh.index[-1]


def test_refresh_failure_preserves_existing_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(price_cache, "CACHE_DIR", str(tmp_path))
    old = _normalized_frame(periods=3)
    old.to_csv(price_cache._path("CRCL"))
    monkeypatch.setattr(price_cache, "_fetch", lambda ticker: None)

    assert price_cache.refresh("CRCL") is None
    cached = price_cache.load("CRCL")
    assert len(cached) == 3
    assert float(cached["close"].iloc[-1]) == float(old["close"].iloc[-1])


def test_refresh_rejects_older_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(price_cache, "CACHE_DIR", str(tmp_path))
    current = _normalized_frame(start="2026-07-10", periods=5)
    current.to_csv(price_cache._path("CRCL"))
    stale = _normalized_frame(start="2026-07-01", periods=2)
    monkeypatch.setattr(price_cache, "_fetch", lambda ticker: stale)

    assert price_cache.refresh("CRCL") is None
    assert price_cache.load("CRCL").index[-1] == current.index[-1]
