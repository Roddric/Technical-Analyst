"""Mechanical bull / bear / sideways classifier (causal, per asset)."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import pandas_ta  # noqa: F401  (registers the .ta accessor)


@dataclass(frozen=True)
class Regime:
    label: str            # "bull" | "bear" | "sideways"
    features: dict


def classify_regime(df: pd.DataFrame) -> Regime:
    close = df["close"].astype("float64")
    ma = close.rolling(config.REGIME_MA_LEN).mean()
    slope = ma.diff(config.REGIME_SLOPE_LB)                 # MA change over the lookback
    adx_df = df.ta.adx(length=config.REGIME_ADX_LEN)
    adx_col = f"ADX_{config.REGIME_ADX_LEN}"
    adx = (adx_df[adx_col] if adx_df is not None and adx_col in adx_df
           else pd.Series(np.nan, index=df.index))

    ma_slope = float(slope.iloc[-1]) if np.isfinite(slope.iloc[-1]) else 0.0
    adx_last = float(adx.iloc[-1]) if np.isfinite(adx.iloc[-1]) else 0.0
    price_vs_ma = float(close.iloc[-1] - ma.iloc[-1]) if np.isfinite(ma.iloc[-1]) else 0.0
    feats = {"ma_slope": ma_slope, "adx": adx_last, "price_vs_ma": price_vs_ma}

    if adx_last < config.REGIME_ADX_TREND:
        return Regime("sideways", feats)
    if ma_slope > 0 and price_vs_ma >= 0:
        return Regime("bull", feats)
    if ma_slope < 0 and price_vs_ma <= 0:
        return Regime("bear", feats)
    return Regime("sideways", feats)
