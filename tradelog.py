"""Trade-plan log + outcome scoring.

Records every ACTIONABLE council plan (long/short with levels; flat/veto skipped)
and later scores each against real prices: a plan stays OPEN until price touches
its stop or target (no time cap); while open it carries a live unrealized P/L.

Design defaults:
  - One open plan per ticker at a time. Re-analyzing a ticker that already has an
    open plan does not log a second one; a new plan can open only after the prior
    one closes.
  - Conservative same-bar resolution: if a single bar's range spans BOTH stop and
    target, it is scored as the stop (loss).

The durable record is meant to live as a Feishu doc the bot maintains; this module
is the working store + scorer, and renders a Feishu-ready markdown table.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import config
config.ensure_reuse_on_path()
from pandasta_data import load_asset

LOG_PATH = Path(__file__).resolve().parent / "results" / "trade_log.jsonl"


# --------------------------------------------------------------------------- #
# Store
# --------------------------------------------------------------------------- #
def _load_all(path: Path = LOG_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _save_all(rows: list[dict], path: Path = LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, default=str) for r in rows) + ("\n" if rows else ""),
                    encoding="utf-8")


def has_open_plan(ticker: str, path: Path = LOG_PATH) -> bool:
    return any(r["ticker"] == ticker and r["status"] == "open" for r in _load_all(path))


# --------------------------------------------------------------------------- #
# Record
# --------------------------------------------------------------------------- #
def record_plan(ticker: str, council: dict, entry_date: str, path: Path = LOG_PATH) -> bool:
    """Append an actionable plan. Returns True if logged, False if skipped
    (not actionable, risk<=0, or a plan is already open for this ticker)."""
    if not council or not council.get("available"):
        return False
    direction = council.get("direction")
    if direction not in ("long", "short") or council.get("veto"):
        return False
    entry, stop, target = council.get("entry"), council.get("stop"), council.get("target")
    if None in (entry, stop, target) or abs(entry - stop) <= 0:
        return False
    if has_open_plan(ticker, path):
        return False

    rows = _load_all(path)
    rows.append({
        "id": f"{ticker}@{entry_date}",
        "ticker": ticker, "entry_date": entry_date,
        "direction": direction, "entry": entry, "stop": stop, "target": target,
        "risk_per_unit": abs(entry - stop),
        "size": council.get("size_fraction"), "conviction": council.get("conviction"),
        "effective_breadth": council.get("effective_breadth"),
        "status": "open", "close_date": None, "exit_price": None,
        "realized_return": None, "realized_R": None,
        "unrealized_return": 0.0, "unrealized_R": 0.0,
        "last_checked": entry_date, "last_price": entry,
    })
    _save_all(rows, path)
    return True


# --------------------------------------------------------------------------- #
# Score
# --------------------------------------------------------------------------- #
def _score_one(plan: dict, bars) -> dict:
    """bars: DataFrame of OHLC strictly AFTER entry_date, ascending. Mutates and
    returns the plan dict."""
    d = 1 if plan["direction"] == "long" else -1
    entry, stop, target, risk = plan["entry"], plan["stop"], plan["target"], plan["risk_per_unit"]
    for ts, row in bars.iterrows():
        hi, lo = float(row["high"]), float(row["low"])
        stop_hit = (lo <= stop) if d == 1 else (hi >= stop)
        target_hit = (hi >= target) if d == 1 else (lo <= target)
        if stop_hit:                       # conservative: stop wins a same-bar tie
            plan.update(status="loss", close_date=str(ts.date()), exit_price=stop,
                        realized_return=(stop - entry) / entry * d,
                        realized_R=(stop - entry) / risk * d)
            return plan
        if target_hit:
            plan.update(status="win", close_date=str(ts.date()), exit_price=target,
                        realized_return=(target - entry) / entry * d,
                        realized_R=(target - entry) / risk * d)
            return plan
    if len(bars):                          # still open -> mark to market
        last_ts, last = bars.index[-1], float(bars["close"].iloc[-1])
        plan.update(last_checked=str(last_ts.date()), last_price=last,
                    unrealized_return=(last - entry) / entry * d,
                    unrealized_R=(last - entry) / risk * d)
    return plan


def update_open_plans(path: Path = LOG_PATH, loader=load_asset) -> dict:
    """Re-score every open plan against fresh prices; persist; return a summary."""
    rows = _load_all(path)
    for plan in rows:
        if plan["status"] != "open":
            continue
        df = loader(plan["ticker"])
        if df is None or df.empty:
            continue
        df = df[df["close"].notna()]
        bars = df[df.index > pd.Timestamp(plan["entry_date"])]
        _score_one(plan, bars)
    _save_all(rows, path)
    return summarize(rows)


def summarize(rows: list[dict]) -> dict:
    closed = [r for r in rows if r["status"] in ("win", "loss")]
    wins = [r for r in closed if r["status"] == "win"]
    open_ = [r for r in rows if r["status"] == "open"]
    realized_R = [r["realized_R"] for r in closed if r["realized_R"] is not None]
    return {
        "n_total": len(rows), "n_open": len(open_), "n_closed": len(closed),
        "n_win": len(wins), "n_loss": len(closed) - len(wins),
        "win_rate": (len(wins) / len(closed)) if closed else None,
        "avg_realized_R": (sum(realized_R) / len(realized_R)) if realized_R else None,
        "total_realized_R": sum(realized_R) if realized_R else 0.0,
        "open_unrealized_R": sum(r["unrealized_R"] for r in open_),
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# Feishu-ready render
# --------------------------------------------------------------------------- #
def render_markdown(summary: dict) -> str:
    s = summary
    wr = f"{s['win_rate']*100:.0f}%" if s["win_rate"] is not None else "—"
    avg = f"{s['avg_realized_R']:+.2f}R" if s["avg_realized_R"] is not None else "—"
    lines = [
        "# Indicator Council — trade log",
        "",
        f"**{s['n_closed']} closed** (win rate {wr}, avg {avg}, total "
        f"{s['total_realized_R']:+.2f}R) · **{s['n_open']} open** "
        f"(unrealized {s['open_unrealized_R']:+.2f}R)",
        "",
        "| ticker | dir | entry_date | entry | stop | target | status | result |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in s["rows"]:
        if r["status"] == "open":
            result = f"open, {r['unrealized_R']:+.2f}R (mtm {r['last_price']})"
        else:
            result = f"{r['status'].upper()} {r['realized_R']:+.2f}R @ {r['close_date']}"
        lines.append(f"| {r['ticker']} | {r['direction']} | {r['entry_date']} | "
                     f"{r['entry']} | {r['stop']} | {r['target']} | {r['status']} | {result} |")
    return "\n".join(lines) + "\n"
