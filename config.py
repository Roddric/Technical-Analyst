"""Central config + reuse shim for the Indicator Council."""
import importlib.metadata  # noqa: F401  preload so pandas_ta imports cleanly standalone
import sys
from pathlib import Path

# Sibling project whose data/indicator/stats code we reuse.
TA_FLAT_DIR = str(Path(__file__).resolve().parent.parent / "ta-flat-backtest")

# Decision
HORIZON = 5                # forward-return horizon (trading days)

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
