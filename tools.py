"""CLI tool interface for OpenClaw / the Feishu bot.

Exposes the tools prompt.py expects as JSON-emitting subcommands:

    python tools.py get_stock_data TICKER [n_rows]
    python tools.py compute_indicators TICKER        # classic suite + council verdict
    python tools.py council TICKER                   # council verdict only

compute_indicators returns the structured classic-TA suite (Layer-1 facts) PLUS
the mechanical council's evidence-weighted verdict under the "council" key, so
OpenClaw can ground its 8-section narrative in both."""
import json
import math
import sys

import config
config.ensure_reuse_on_path()

import indicators as ind
import run


def _clean(obj):
    """Recursively replace non-finite floats with None so output is strict JSON."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


def council_verdict(ticker: str) -> dict:
    """The mechanical arm's evidence-weighted read, as a compact dict."""
    p = run.analyze_ticker(ticker)
    if p is None:
        return {"available": False, "reason": "no data / insufficient history"}
    return {
        "available": True,
        "direction": {1: "long", -1: "short", 0: "flat"}[p.direction],
        "conviction": round(p.conviction, 3),
        "effective_breadth": round(p.effective_n, 2),
        "max_inter_set_corr": round(p.decorrelation.get("max_abs_corr", 0.0), 2),
        "veto": p.veto,
        "entry": round(p.entry, 4), "stop": round(p.stop, 4),
        "target": round(p.target, 4), "size_fraction": round(p.size, 5),
        "set_contributions": {k: round(v, 4) for k, v in p.set_contributions.items()},
        "note": "direction/conviction are a deterministic function of out-of-sample "
                "IC; every number is rule-derived. eff_breadth<1.5 => one set dominates.",
    }


def get_stock_data(ticker: str, n_rows: int = 180) -> dict:
    df = ind.get_stock_data(ticker)
    if df is None:
        return {"ticker": ticker, "error": "no data"}
    tail = df.tail(n_rows)
    rows = [{"date": str(idx.date()), "open": round(float(r.open), 4),
             "high": round(float(r.high), 4), "low": round(float(r.low), 4),
             "close": round(float(r.close), 4), "volume": float(r.volume)}
            for idx, r in tail.iterrows()]
    return {"ticker": ticker, "n_rows": len(rows), "interval": "1d", "rows": rows}


def compute_indicators(ticker: str) -> dict:
    df = ind.get_stock_data(ticker)
    if df is None:
        return {"ticker": ticker, "error": "no data"}
    out = ind.compute_indicators(df)
    out["ticker"] = ticker
    out["council"] = council_verdict(ticker)
    return out


_DISPATCH = {
    "get_stock_data": lambda a: get_stock_data(a[0], int(a[1]) if len(a) > 1 else 180),
    "compute_indicators": lambda a: compute_indicators(a[0]),
    "council": lambda a: council_verdict(a[0]),
}


def main(argv=None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] not in _DISPATCH:
        print(json.dumps({"error": "usage: tools.py <get_stock_data|compute_indicators|"
                                    "council> TICKER [n_rows]",
                          "commands": list(_DISPATCH)}, indent=2))
        return
    result = _clean(_DISPATCH[argv[0]](argv[1:]))
    print(json.dumps(result, indent=2, allow_nan=False, default=str))


if __name__ == "__main__":
    main()
