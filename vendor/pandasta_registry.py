"""
pandasta_registry.py
====================
Curated enumeration of pandas_ta indicators at DEFAULT parameters for the four
slots (volume, trend, momentum, volatility).

Rules (mirrors indicators.py design):
  * No raw price-LEVEL outputs (MA-type lines, band levels, trailing stops).
    Band information enters only as %B or normalized width.
  * Everything must be causal: indicator[t] depends only on bars <= t.
    dpo is forced centered=False (pandas_ta default is centered = lookahead).
    zigzag / ichimoku-style forward or repainting outputs are excluded.
  * Multi-column outputs contribute ONE explicit primary column.
Probed against pandas_ta 0.4.24 on 2026-07-06.
"""
from __future__ import annotations

import importlib.metadata  # noqa: F401  (must precede pandas_ta on py3.14)
from dataclasses import dataclass, field

import warnings

import numpy as np
import pandas as pd
import pandas_ta as ta  # noqa: F401  (df.ta accessor)
from pandas_ta.core import AnalysisIndicators as _PandasTAAccessor

SLOTS = ("volume", "trend", "momentum", "volatility")


def _ensure_pandas_ta_accessor() -> None:
    """The 'ta' DataFrame accessor is contested: pandas_ta_classic (if
    installed and imported anywhere) registers the same name. Whichever library
    registers last wins process-wide, so if anything has re-registered 'ta'
    after us, silently reclaim it before computing.

    Note: pd.DataFrame.ta accessed at the class level (obj=None) returns
    pandas's CachedAccessor.__get__ result, which for obj is None returns
    the registered accessor *class* itself (not a CachedAccessor wrapper
    instance) -- see pandas.core.accessor.Accessor.__get__. So the identity
    check is against pd.DataFrame.ta directly, not a nested ._accessor
    attribute. Verified against pandas 3.0.3.
    """
    current = getattr(pd.DataFrame, "ta", None)
    if current is not _PandasTAAccessor:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            pd.api.extensions.register_dataframe_accessor("ta")(_PandasTAAccessor)

# fn -> reason, for the audit trail in reports
EXCLUDED = {
    "psar": "trailing-stop price levels (PSARl/PSARs)",
    "smc": "multi-structure output, no scalar primary line",
    "exhc": "sparse exhaustion counts, mostly NaN",
    "squeeze_pro": "duplicate of squeeze with binary flags",
    "ht_trendline": "raw price level",
    "decay": "utility transform, not a signal",
    "increasing": "binary utility",
    "decreasing": "binary utility",
    "long_run": "requires external fast/slow inputs",
    "short_run": "requires external fast/slow inputs",
    "tsignals": "requires external trend input",
    "xsignals": "requires external signal input",
    "zigzag": "repaints (non-causal by construction)",
    "amat": "binary state pair",
    "rwi": "paired high/low lines, no scalar primary",
    "alphatrend": "trailing price level",
    "cksp": "stop price levels",
    "atrts": "trailing-stop price level",
    "aberration": "band price levels",
    "accbands": "band price levels (width captured as derived ACCB_WIDTH)",
    "donchian": "band price levels (width captured as derived DC_WIDTH)",
    "kc": "band price levels (width captured as derived KC_WIDTH)",
    "hwc": "channel price levels",
    "chandelier_exit": "stop price levels",
    "atr": "price-scaled; normalized form kept as natr + derived ATR_RATIO",
    "true_range": "price-scaled level",
    "pdist": "price-scaled level",
    "thermo": "price-difference-scaled level",
    "bbands": "band levels; %B kept as primary column candidate",
    "vwap": "anchored intraday concept + price level",
    "vwma": "raw price level",
    "pvol": "price*volume trending level",
    "pvr": "1-4 categorical code",
    "aobv": "bundle incl. binary run flags",
    "kdj": "kept via stoch (K duplicates)",
    "vhm": "mostly NaN on daily data",
}

# fn -> primary output column (multi-column outputs only)
PRIMARY_COL = {
    "brar": "AR_26",
    "eri": "BULLP_13",
    "fisher": "FISHERT_9_1",
    "kst": "KST_10_15_20_30_10_10_10_15",
    "macd": "MACDh_12_26_9",
    "ppo": "PPOh_12_26_9",
    "qqe": "QQE_14_5_4.236",
    "rvgi": "RVGI_14_4",
    "smi": "SMI_5_20_5_1.0",
    "squeeze": "SQZ_20_2.0_20_1.5",
    "stc": "STC_10_12_26_0.5",
    "stoch": "STOCHk_14_3_3",
    "stochf": "STOCHFk_14_3",
    "stochrsi": "STOCHRSIk_14_14_3_3",
    "tmo": "TMO_14_5_3",
    "trix": "TRIX_30_9",
    "tsi": "TSI_13_25_13",
    "adx": "ADX_14",
    "aroon": "AROONOSC_14",
    "vortex": "VTXP_14",
    "kvo": "KVO_34_55_13",
    "pvi": "PVI",
    "pvo": "PVOh_12_26_9",
    "wb_tsv": "TSV_18_10",
    "bbands": "BBP_5_2.0",
}

PER_FN_KWARGS = {
    "dpo": {"centered": False},  # pandas_ta default centered=True is lookahead
}

SLOT_PREFIX = {"momentum": "MO", "trend": "TR", "volatility": "VO", "volume": "VU"}


@dataclass(frozen=True)
class Candidate:
    name: str
    slot: str
    fn: str                 # pandas_ta accessor name, or derived key
    column: str | None      # column when output is a DataFrame
    kwargs: dict = field(default_factory=dict)
    uses_volume: bool = False
    derived: str | None = None  # None | "atr_ratio" | "kc_width" | "dc_width" | "accb_width"


def _derived_candidates() -> list[Candidate]:
    return [
        Candidate("VO-ATR_RATIO", "volatility", "atr_ratio", None, {}, False, "atr_ratio"),
        Candidate("VO-KC_WIDTH", "volatility", "kc_width", None, {}, False, "kc_width"),
        Candidate("VO-DC_WIDTH", "volatility", "dc_width", None, {}, False, "dc_width"),
        Candidate("VO-ACCB_WIDTH", "volatility", "accb_width", None, {}, False, "accb_width"),
        Candidate("VO-BBP", "volatility", "bbands", "BBP_5_2.0", {}, False, None),
    ]


def build_candidates() -> list[Candidate]:
    cats = {s: sorted(ta.Category[s]) for s in SLOTS}
    volume_fns = set(cats["volume"])
    out: list[Candidate] = []
    for slot in SLOTS:
        for fn in cats[slot]:
            if fn in EXCLUDED:
                continue
            name = f"{SLOT_PREFIX[slot]}-{fn}"
            out.append(Candidate(
                name=name, slot=slot, fn=fn,
                column=PRIMARY_COL.get(fn),
                kwargs=PER_FN_KWARGS.get(fn, {}),
                uses_volume=(fn in volume_fns),
            ))
    out.extend(_derived_candidates())
    return out


def _band_width(df: pd.DataFrame, method: str) -> pd.Series:
    if method == "kc_width":
        b = df.ta.kc()
        w = (b["KCUe_20_2"] - b["KCLe_20_2"]) / b["KCBe_20_2"]
    elif method == "dc_width":
        b = df.ta.donchian()
        w = (b["DCU_20_20"] - b["DCL_20_20"]) / b["DCM_20_20"]
    elif method == "accb_width":
        b = df.ta.accbands()
        w = (b["ACCBU_20"] - b["ACCBL_20"]) / b["ACCBM_20"]
    else:
        raise ValueError(method)
    return w


def compute_candidate(df: pd.DataFrame, cand: Candidate) -> pd.Series:
    """Compute one candidate on a normalized OHLCV frame. Returns float64
    Series aligned to df.index (NaN where undefined). Raises on failure —
    caller decides whether to skip."""
    _ensure_pandas_ta_accessor()
    if cand.derived == "atr_ratio":
        x = df.ta.atr() / df["close"]
        out = x
    elif cand.derived in ("kc_width", "dc_width", "accb_width"):
        out = _band_width(df, cand.derived)
    else:
        res = getattr(df.ta, cand.fn)(**cand.kwargs)
        if res is None:
            raise ValueError(f"{cand.fn} returned None")
        if isinstance(res, pd.DataFrame):
            if cand.column is None or cand.column not in res.columns:
                raise ValueError(f"{cand.fn}: primary column {cand.column!r} "
                                 f"not in {list(res.columns)}")
            out = res[cand.column]
        else:
            out = res
    out = pd.to_numeric(out, errors="coerce").astype("float64")
    out = out.replace([np.inf, -np.inf], np.nan)
    return out.reindex(df.index)
