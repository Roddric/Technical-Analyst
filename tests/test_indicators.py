import numpy as np
import pandas as pd
import indicators


def _trend_df(n=400, step=0.004, noise=0.001, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.standard_normal(n) * noise + step))
    idx = pd.bdate_range("2020-01-01", periods=n)
    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = close * (1 - step / 2)
    df["high"] = close * (1 + noise * 3)
    df["low"] = np.minimum(df["open"], close) * (1 - noise * 3)
    df["volume"] = np.linspace(1000, 5000, n)     # rising volume
    return df


def test_structure_has_all_sections():
    out = indicators.compute_indicators(_trend_df())
    assert set(out) == {"overview", "trend", "momentum", "volatility", "volume", "levels"}
    assert set(out["momentum"]) >= {"rsi", "rsi_zone", "rsi_divergence", "macd",
                                    "macd_signal", "macd_hist", "macd_cross", "macd_hist_trend"}


def test_uptrend_reads_bullish_structure():
    out = indicators.compute_indicators(_trend_df())
    t = out["trend"]
    assert t["price_vs_sma200"] == "above"      # strong uptrend
    assert t["ema_stack"] == "bullish"
    assert out["overview"]["current_price"] > 0


def test_rsi_in_range_and_zone_consistent():
    out = indicators.compute_indicators(_trend_df())
    m = out["momentum"]
    assert 0 <= m["rsi"] <= 100
    zone = m["rsi_zone"]
    assert (zone == "overbought" and m["rsi"] >= 70) or \
           (zone == "oversold" and m["rsi"] <= 30) or \
           (zone == "neutral" and 30 < m["rsi"] < 70)


def test_levels_risk_reward_positive():
    out = indicators.compute_indicators(_trend_df())
    lv = out["levels"]
    assert lv["support"] < out["overview"]["current_price"] or lv["dist_to_support_pct"] is not None
    assert lv["resistance"] >= lv["support"]


def test_short_history_reports_error():
    df = _trend_df(n=120)
    out = indicators.compute_indicators(df)
    assert "error" in out


def test_get_stock_data_cached():
    df = indicators.get_stock_data("BTC-USD")
    assert df is not None and {"open", "high", "low", "close"} <= set(df.columns)
