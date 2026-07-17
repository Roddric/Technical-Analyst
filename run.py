"""Mechanical pipeline: prices -> regime -> sets -> (FDR-gated) weights -> decision -> plan."""
import json
import sys
from pathlib import Path

import config
config.ensure_reuse_on_path()
from pandasta_data import UNIVERSE, load_asset, return_mode

import regime as regime_mod
import sets as sets_mod
import selection as selection_mod
import evidence as evidence_mod
import arbiter as arbiter_mod
import risk as risk_mod
import plan as plan_mod
import report as report_mod

RESULTS = Path(__file__).resolve().parent / "results"


def _safe_return_mode(ticker: str) -> str:
    try:
        return return_mode(ticker)
    except KeyError:
        return "log"          # arbitrary tickers default to log returns


def analyze_ticker(ticker: str, mode: str | None = None) -> plan_mod.Plan | None:
    """On-demand single-ticker read. Works for any Yahoo ticker (load_asset fetches
    + caches), not just the basket. Marginal t-gate (no cross-asset FDR)."""
    df = load_asset(ticker)
    if df is not None:
        df = df[df["close"].notna()]          # drop trailing/partial NaN-close bars
    if df is None or len(df) < config.REGIME_MA_LEN + config.HORIZON:
        return None
    return analyze_asset(df, ticker, mode or _safe_return_mode(ticker), roster_key=ticker)


def analyze_asset(df, asset: str, mode: str = "log", allowed=None,
                  roster_key: str | None = None) -> plan_mod.Plan:
    reg = regime_mod.classify_regime(df)          # context only; never feeds the arbiter
    signals = selection_mod.build_selected_sets(df, mode, roster_key=roster_key)
    weights = evidence_mod.compute_weights(signals, df, mode, allowed=allowed)
    latest = {n: (float(s.iloc[-1]) if s.notna().iloc[-1] else 0.0)
              for n, s in signals.items()}
    decision = arbiter_mod.arbitrate(latest, weights, long_only=config.LONG_ONLY)
    levels = risk_mod.build_levels(df, decision)
    decorr = sets_mod.check_decorrelation(signals, config.DECORR_THRESHOLD)
    return plan_mod.assemble_plan(asset, reg, decision, levels, decorr)


def run_universe(assets=None) -> list[plan_mod.Plan]:
    assets = assets or list(UNIVERSE)
    loaded = []
    pvals = {}
    # Pass 1: per-asset set stats -> grid of one-sided p-values.
    for a in assets:
        df = load_asset(a)
        if df is not None:
            df = df[df["close"].notna()]
        if df is None or len(df) < config.REGIME_MA_LEN + config.HORIZON:
            continue
        mode = return_mode(a)
        signals = selection_mod.build_selected_sets(df, mode, roster_key=a)
        stats = evidence_mod.set_ic_stats(signals, df, mode)
        loaded.append((a, df, mode))
        for name, (_ic, t, _n) in stats.items():
            pvals[(a, name)] = evidence_mod.one_sided_p(t)
    # FDR across the whole (asset x set) grid.
    survivors = evidence_mod.fdr_survivors(pvals, config.FDR_Q)
    # Pass 2: weight only survivors, per asset.
    plans = []
    for a, df, mode in loaded:
        allowed = {name for (asset_k, name) in survivors if asset_k == a}
        plans.append(analyze_asset(df, a, mode, allowed=allowed, roster_key=a))
    return plans


def _print_line(p: plan_mod.Plan) -> None:
    arrow = {1: "LONG", -1: "SHORT", 0: "FLAT"}[p.direction]
    tail = "VETO" if p.veto else \
        f"entry={p.entry:.2f} stop={p.stop:.2f} tgt={p.target:.2f}"
    print(f"{p.asset:<10} {p.regime_label:<9} {arrow:<6} "
          f"conv={p.conviction:.2f} eff_n={p.effective_n:.2f} "
          f"corr={p.decorrelation.get('max_abs_corr', 0):.2f} {tail}")


def main(argv=None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    RESULTS.mkdir(exist_ok=True)
    if argv:                                     # on-demand: one or more tickers
        for ticker in argv:
            p = analyze_ticker(ticker)
            if p is None:
                print(f"{ticker}: no data / insufficient history")
                continue
            path = report_mod.write_report(p, RESULTS)
            _print_line(p)
            print(f"  -> {path}")
        return
    plans = run_universe()                       # default: whole basket
    (RESULTS / "plans_latest.json").write_text(
        json.dumps([p.to_dict() for p in plans], indent=2))
    for p in plans:
        _print_line(p)


if __name__ == "__main__":
    main()
