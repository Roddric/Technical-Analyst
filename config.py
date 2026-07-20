"""Central config + reuse shim for the Indicator Council."""
import importlib.metadata  # noqa: F401  preload so pandas_ta imports cleanly standalone
import sys
from pathlib import Path

# Vendored data/indicator/stats modules (self-contained; no sibling dependency).
TA_FLAT_DIR = str(Path(__file__).resolve().parent / "vendor")

# Decision
HORIZON = 5                # forward-return horizon (trading days)
LONG_ONLY = True           # policy: suppress short signals to flat (no short positions)

# Cross-market linkage (Phase A: SK Hynix ADR)
XMKT_Z_WINDOW = 60          # trailing window for causal z-scores
XMKT_MIN_HISTORY = 150      # aligned finite bars required before a signal is emitted
# adr_ratio = ADRs per local share (10 SKHY ADRs = 1 000660.KS share, SEC
# prospectus). Formula: premium = adr_usd * fx * adr_ratio / local - 1 (scales the
# ADR up to a full-share basis). NOTE: this is 10, NOT 0.1 — the ratio multiplies
# the ADR side; "1 ADR = 1/10 share" encodes here as 10 ADRs-per-share.
# Phase B: 7709.HK is the HK-listed 2x-daily-leveraged ETF on 000660.KS. The
# anchor is the PLAIN KRW return with NO FX term — settled empirically, not by
# argument (regression on n=159: KRW anchor R2=0.933/beta=1.78 beats the
# HKD-translated R2=0.920). `leverage` is the NOMINAL 2.0; the causal z-score
# de-means the systematic 2-vs-1.78 tracking friction, so no rolling beta fit is
# needed. `substitute` is the Korea-holiday fallback anchor.
# Two-way ADR<->local conversion opens 2026-07-29 for SK Hynix. BEFORE it, the
# premium is a ONE-WAY scarcity premium with no arbitrage force to parity, so
# xmkt_adr_premium's mean-reversion premise does NOT hold yet. Do not pool
# pre/post history in one window for IC testing — split on this date.
ADR_TWO_WAY_CONVERSION_DATE = "2026-07-29"
# regime_start belongs to the PAIR, not the module: it marks where two-way
# conversion began, and is None for any ADR that has had two-way conversion for
# the whole sample (the normal, mature case). A module-level default would
# silently apply SK Hynix's date to unrelated pairs and gate their entire
# history away — which is indistinguishable from "no edge found".
CROSS_MARKET_MAP = {        # target ticker -> foreign legs (yfinance symbols)
    "000660.KS": {"adr": "SKHY", "fx": "KRW=X", "adr_ratio": 10.0,
                  "regime_start": ADR_TWO_WAY_CONVERSION_DATE},
    # TSMC: a MATURE dual-listing used to validate the METHOD, not to shortcut
    # SK Hynix. 1 TSM ADR = 5 ordinary 2330.TW shares, so ADRs-per-local-share
    # = 0.2. Two-way conversion has run normally for decades -> no regime split.
    "2330.TW": {"adr": "TSM", "fx": "TWD=X", "adr_ratio": 0.2,
                "regime_start": None},
    # Mature dual-listings, deliberately spread across sector/region/regime so a
    # shared result cannot be an artifact of picking similar names. Ratios are
    # prospectus facts, each confirmed against the implied par ratio (the ratio
    # that would put today's premium at 0) — a units check, not a signal fit:
    #   7203.T    assumed 0.10  implied 0.1005    (1 TM ADR = 10 ordinary)
    #   NOVO-B.CO assumed 1.00  implied 1.0037    (1 NVO ADR = 1 ordinary)
    #   SHEL.L    assumed 50.0  implied 49.889    (1 SHEL ADR = 2 ordinary, and
    #                                              the LSE quotes in PENCE: 0.5*100)
    "7203.T": {"adr": "TM", "fx": "JPY=X", "adr_ratio": 0.1, "regime_start": None},
    "NOVO-B.CO": {"adr": "NVO", "fx": "DKK=X", "adr_ratio": 1.0, "regime_start": None},
    "SHEL.L": {"adr": "SHEL", "fx": "GBP=X", "adr_ratio": 50.0, "regime_start": None},
    "7709.HK": {"underlying": "000660.KS", "substitute": "SKHY", "leverage": 2.0},
}
# Post-regime bars required before xmkt_adr_premium emits again. Same evidence
# bar as XMKT_MIN_HISTORY, keyed to days-since-REGIME-start instead of
# days-since-DATA-start; kept separate so the regime gate can be tuned without
# touching the history gate. Until it is met the signal is simply absent —
# honest emptiness, not a contaminated number.
XMKT_REGIME_MIN_BARS = XMKT_MIN_HISTORY

# Sets / decorrelation
N_PERSONALITIES = 3        # legacy round-robin roster size (superseded by selection)
DECORR_THRESHOLD = 0.6     # max allowed |corr| between set (error) series
SLOT_KEEP = 4              # top-K decorrelated indicators kept per slot before bundling
MAX_SETS = 6               # cap on the greedily-selected decorrelated roster
ERR_WINDOW = 63            # rolling window for the error (rolling-IC) series

# Evidence weighting (unified power-gate + shrink via the HAC t-stat)
TRAIN_FRAC = 0.7           # fit member signs on the first fraction; measure IC on the holdout
GATE_K = 1.65              # min HAC t to trust a set; weight proportional to max(0, ic*(1 - k/t))
FDR_Q = 0.10               # Benjamini-Hochberg q across the (asset x set) grid
NULL_SEED = 12345          # seed for the always-on null tripwire set

# Risk (rule-derived plan numbers)
ATR_LEN = 14
ATR_MULT_STOP = 2.0
R_MULTIPLE = 2.0
RISK_BUDGET = 0.005        # fraction of capital risked per trade

# Regime classifier
REGIME_MA_LEN = 100
REGIME_SLOPE_LB = 20
REGIME_ADX_LEN = 14
REGIME_ADX_TREND = 20.0    # ADX above -> trending; below -> sideways


def ensure_reuse_on_path() -> None:
    """Make the ta-flat-backtest modules importable."""
    if TA_FLAT_DIR not in sys.path:
        sys.path.insert(0, TA_FLAT_DIR)
