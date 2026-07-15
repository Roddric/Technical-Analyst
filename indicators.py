"""compute_indicators / get_stock_data — the tools OpenClaw calls.

Returns the classic TA suite as STRUCTURED DATA with mechanical signals only
(Layer-1 facts: raw value + the signal it mechanically produces). No narrative,
no interpretation-in-context — OpenClaw's prompt does the layered reasoning.
Every indicator is computed on full history (so SMA200 etc. are valid) and the
last-bar reading is reported."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import pandas_ta  # noqa: F401
from pandasta_data import load_asset

PERIOD_BARS = 126          # ~6 months of trading days for period-window stats


def get_stock_data(ticker: str, period_days: int | None = None) -> pd.DataFrame | None:
    """Full cached/fetched OHLCV (any Yahoo ticker). Indicators need long lookback,
    so we return full history; `period_days` optionally tail-trims for callers that
    only want the recent window."""
    df = load_asset(ticker)
    if df is None or df.empty:
        return None
    df = df[df["close"].notna()]          # drop trailing/partial NaN-close bars
    if df.empty:
        return None
    return df.tail(period_days).copy() if period_days else df


def _last(s: pd.Series) -> float:
    return float(s.iloc[-1]) if s is not None and len(s) and np.isfinite(s.iloc[-1]) else float("nan")


def _pos(price: float, level: float) -> str:
    if not np.isfinite(level):
        return "n/a"
    return "above" if price > level else "below"


def _overview(df: pd.DataFrame) -> dict:
    close = df["close"]
    price = _last(close)
    win = df.tail(PERIOD_BARS)
    hi, lo = float(win["high"].max()), float(win["low"].min())
    return {
        "current_price": round(price, 2),
        "period_start": str(win.index[0].date()),
        "period_end": str(win.index[-1].date()),
        "n_bars_total": int(len(df)),
        "period_high": round(hi, 2),
        "period_low": round(lo, 2),
        "pct_from_high": round(100 * (price - hi) / hi, 2) if hi else None,
        "pct_from_low": round(100 * (price - lo) / lo, 2) if lo else None,
    }


def _cross(fast: pd.Series, slow: pd.Series):
    """Most recent cross of fast over/under slow: (type, date) or (None, None)."""
    d = (fast - slow).dropna()
    if len(d) < 2:
        return None, None
    sign = np.sign(d)
    flips = sign.ne(sign.shift())
    idx = d.index[flips.fillna(False)]
    if len(idx) == 0:
        return None, None
    last = idx[-1]
    kind = "golden_cross" if d.loc[last] > 0 else "death_cross"
    return kind, str(pd.Timestamp(last).date())


def _trend(df: pd.DataFrame) -> dict:
    close = df["close"]
    price = _last(close)
    sma20, sma50, sma200 = (close.rolling(n).mean() for n in (20, 50, 200))
    ema20, ema50 = (close.ewm(span=n, adjust=False).mean() for n in (20, 50))
    kind, date = _cross(sma50, sma200)
    e20, e50 = _last(ema20), _last(ema50)
    return {
        "sma20": round(_last(sma20), 2), "sma50": round(_last(sma50), 2),
        "sma200": round(_last(sma200), 2),
        "price_vs_sma20": _pos(price, _last(sma20)),
        "price_vs_sma50": _pos(price, _last(sma50)),
        "price_vs_sma200": _pos(price, _last(sma200)),
        "ema20": round(e20, 2), "ema50": round(e50, 2),
        "ema_stack": "bullish" if e20 > e50 else "bearish",
        "sma50_200_cross": kind, "cross_date": date,
    }


def _rsi_divergence(close: pd.Series, rsi: pd.Series, window: int = 40) -> str:
    c, r = close.tail(window), rsi.tail(window)
    if len(c) < window:
        return "none"
    half = window // 2
    p_prev, p_now = c.iloc[:half], c.iloc[half:]
    r_prev, r_now = r.iloc[:half], r.iloc[half:]
    if p_now.min() < p_prev.min() and r_now.min() > r_prev.min():
        return "bullish"      # price lower low, RSI higher low
    if p_now.max() > p_prev.max() and r_now.max() < r_prev.max():
        return "bearish"      # price higher high, RSI lower high
    return "none"


def _momentum(df: pd.DataFrame) -> dict:
    close = df["close"]
    rsi = df.ta.rsi(length=14)
    rsi_v = _last(rsi)
    zone = "overbought" if rsi_v >= 70 else "oversold" if rsi_v <= 30 else "neutral"
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    line = macd["MACD_12_26_9"]; sig = macd["MACDs_12_26_9"]; hist = macd["MACDh_12_26_9"]
    h_now, h_prev = _last(hist), (float(hist.iloc[-4]) if len(hist) >= 4 and np.isfinite(hist.iloc[-4]) else float("nan"))
    hist_trend = "expanding" if abs(h_now) > abs(h_prev) else "contracting"
    return {
        "rsi": round(rsi_v, 2), "rsi_zone": zone,
        "rsi_divergence": _rsi_divergence(close, rsi),
        "macd": round(_last(line), 4), "macd_signal": round(_last(sig), 4),
        "macd_hist": round(h_now, 4),
        "macd_cross": "bullish" if _last(line) > _last(sig) else "bearish",
        "macd_hist_trend": hist_trend,
    }


def _volatility(df: pd.DataFrame) -> dict:
    close = df["close"]; price = _last(close)
    bb = df.ta.bbands(length=20, std=2)
    lower = bb.filter(like="BBL_").iloc[:, 0]
    mid = bb.filter(like="BBM_").iloc[:, 0]
    upper = bb.filter(like="BBU_").iloc[:, 0]
    width = (upper - lower) / mid
    pb = (price - _last(lower)) / (_last(upper) - _last(lower)) if _last(upper) != _last(lower) else float("nan")
    w_now = _last(width)
    squeeze = bool(np.isfinite(w_now) and w_now <= np.nanpercentile(width.tail(PERIOD_BARS), 20))
    atr = df.ta.atr(length=14)
    atr_v = _last(atr)
    w_prev = float(width.iloc[-6]) if len(width) >= 6 and np.isfinite(width.iloc[-6]) else float("nan")
    return {
        "bb_upper": round(_last(upper), 2), "bb_mid": round(_last(mid), 2),
        "bb_lower": round(_last(lower), 2), "percent_b": round(pb, 3),
        "bb_squeeze": squeeze,
        "atr": round(atr_v, 4), "atr_pct": round(100 * atr_v / price, 2) if price else None,
        "expected_daily_range": round(atr_v, 2),
        "volatility_direction": "expanding" if w_now > w_prev else "contracting",
    }


def _volume(df: pd.DataFrame, window: int = 20) -> dict:
    if "volume" not in df or df["volume"].fillna(0).le(0).all():
        return {"available": False}
    obv = df.ta.obv()
    obv_slope = float(obv.iloc[-1] - obv.iloc[-window]) if len(obv) > window else float("nan")
    price_slope = float(df["close"].iloc[-1] - df["close"].iloc[-window]) if len(df) > window else float("nan")
    strength = (abs(obv_slope) / (abs(obv).tail(window).mean() + 1e-9))
    confirm = np.sign(obv_slope) == np.sign(price_slope)
    div = "none"
    if not confirm:
        div = "bullish_accumulation" if obv_slope > 0 > price_slope else "bearish_distribution"
    return {
        "available": True,
        "obv_trend": "rising" if obv_slope > 0 else "falling",
        "obv_strength": "strong" if strength > 0.5 else "moderate" if strength > 0.1 else "weak",
        "price_confirmation": bool(confirm),
        "divergence": div,
    }


def _levels(df: pd.DataFrame, lookback: int = 60) -> dict:
    close = df["close"]; price = _last(close)
    win = df.tail(lookback)
    resistance = float(win["high"].max())
    support = float(win["low"].min())
    up = resistance - price
    down = price - support
    return {
        "support": round(support, 2), "resistance": round(resistance, 2),
        "dist_to_support_pct": round(100 * down / price, 2) if price else None,
        "dist_to_resistance_pct": round(100 * up / price, 2) if price else None,
        "risk_reward": round(up / down, 2) if down > 0 else None,
    }


def compute_indicators(df: pd.DataFrame) -> dict:
    """Structured classic-TA suite with mechanical signals. Raises if df too short."""
    if df is None or len(df) < 200:
        return {"error": "insufficient history (need >= 200 bars for SMA200)",
                "n_bars": 0 if df is None else len(df)}
    return {
        "overview": _overview(df),
        "trend": _trend(df),
        "momentum": _momentum(df),
        "volatility": _volatility(df),
        "volume": _volume(df),
        "levels": _levels(df),
    }
