"""Automated daily technical reports with a durable seven-day review.

The deterministic engine remains the source of every indicator and council
number.  This module adds orchestration only:

1. optionally refresh the pinned market-data cache;
2. compute the current indicator packet;
3. compare it with archived reports from the prior seven calendar days;
4. score matured archived directional calls on a forward basis;
5. write Markdown + JSON archives and optionally notify Feishu.

The archive scorecard is prospective validation, not a substitute for a full
portfolio backtest.  It deliberately reports "insufficient sample" until enough
daily reports have matured.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile
from urllib import request

import pandas as pd

import indicators
import tools

DEFAULT_CONFIG = Path(__file__).resolve().parent / "daily-report.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "reports" / "daily"
DEFAULT_REVIEW_DAYS = 7
DEFAULT_VALIDATION_HORIZON = 5
MIN_VALIDATION_SAMPLE = 20


def _safe_ticker(ticker: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", ticker).strip("_") or "asset"


def _clean_json(obj):
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): _clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_json(v) for v in obj]
    return obj


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    if not path.exists():
        return {
            "assets": [{"ticker": "CRCL", "name": "Circle Internet Group"}],
            "review_days": DEFAULT_REVIEW_DAYS,
            "validation_horizon": DEFAULT_VALIDATION_HORIZON,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("assets"), list) or not data["assets"]:
        raise ValueError("daily-report config must contain a non-empty 'assets' list")
    return data


def load_archives(output_dir: Path, ticker: str) -> list[dict]:
    """Load dated snapshots only; ``latest.json`` is intentionally excluded."""
    root = output_dir / _safe_ticker(ticker)
    snapshots = []
    if not root.exists():
        return snapshots
    for path in sorted(root.glob("????-??-??.json")):
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if snapshot.get("ticker") == ticker and snapshot.get("market_asof"):
            snapshots.append(snapshot)
    return snapshots


def _packet_value(snapshot: dict, *keys, default=None):
    value = snapshot.get("indicators", {})
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return default if value is None else value


def _council_state(snapshot: dict) -> str:
    council = _packet_value(snapshot, "council", default={})
    if not council or not council.get("available"):
        return "unavailable"
    if council.get("long_only_suppressed"):
        return "bearish / suppressed"
    return str(council.get("direction", "unknown"))


def review_recent(previous: list[dict], current: dict,
                  review_days: int = DEFAULT_REVIEW_DAYS) -> dict:
    current_day = date.fromisoformat(current["market_asof"])
    cutoff = current_day - timedelta(days=review_days)
    recent = [
        s for s in previous
        if cutoff <= date.fromisoformat(s["market_asof"]) < current_day
    ]
    recent.sort(key=lambda s: s["market_asof"])
    series = recent + [current]
    rows = []
    for snapshot in series:
        rows.append({
            "market_asof": snapshot["market_asof"],
            "price": _packet_value(snapshot, "overview", "current_price"),
            "rsi": _packet_value(snapshot, "momentum", "rsi"),
            "macd_cross": _packet_value(snapshot, "momentum", "macd_cross"),
            "ema_stack": _packet_value(snapshot, "trend", "ema_stack"),
            "council_state": _council_state(snapshot),
            "conviction": _packet_value(snapshot, "council", "conviction"),
        })

    price_change_pct = None
    if len(rows) > 1 and rows[0]["price"] not in (None, 0) and rows[-1]["price"] is not None:
        price_change_pct = 100.0 * (rows[-1]["price"] / rows[0]["price"] - 1.0)

    transitions = []
    for before, after in zip(rows, rows[1:]):
        if before["council_state"] != after["council_state"]:
            transitions.append({
                "from_date": before["market_asof"],
                "to_date": after["market_asof"],
                "from": before["council_state"],
                "to": after["council_state"],
            })

    rsi_values = [r["rsi"] for r in rows if r["rsi"] is not None]
    return {
        "window_days": review_days,
        "prior_reports_found": len(recent),
        "window_start": rows[0]["market_asof"] if rows else current["market_asof"],
        "window_end": current["market_asof"],
        "price_change_pct": price_change_pct,
        "rsi_min": min(rsi_values) if rsi_values else None,
        "rsi_max": max(rsi_values) if rsi_values else None,
        "council_transitions": transitions,
        "rows": rows,
    }


def _forecast_direction(snapshot: dict) -> int | None:
    council = _packet_value(snapshot, "council", default={})
    if not council or not council.get("available"):
        return None
    if council.get("long_only_suppressed"):
        return -1
    return {"long": 1, "short": -1}.get(council.get("direction"))


def validate_archived_forecasts(snapshots: list[dict], df: pd.DataFrame,
                                horizon: int = DEFAULT_VALIDATION_HORIZON,
                                min_sample: int = MIN_VALIDATION_SAMPLE) -> dict:
    """Score archived council directions after ``horizon`` trading bars.

    Each archive was generated using only information then available. Genuine
    flats are abstentions; long-only-suppressed bearish reads are scored short
    for diagnostic purposes even though no trade was taken.
    """
    if df is None or len(df) == 0:
        return {
            "status": "no market data", "horizon_bars": horizon,
            "n_directional": 0, "n_matured": 0, "n_pending": 0,
            "n_abstained": len(snapshots), "outcomes": [],
        }

    frame = df[df["close"].notna()].copy()
    frame.index = pd.DatetimeIndex(frame.index).normalize()
    pos_by_day = {str(ts.date()): i for i, ts in enumerate(frame.index)}
    # A rerun on the same market date replaces that date's forecast.
    unique = {s["market_asof"]: s for s in snapshots}
    outcomes = []
    abstained = 0
    pending = 0
    for market_asof, snapshot in sorted(unique.items()):
        direction = _forecast_direction(snapshot)
        if direction is None:
            abstained += 1
            continue
        start = pos_by_day.get(market_asof)
        if start is None:
            continue
        end = start + horizon
        if end >= len(frame):
            pending += 1
            continue
        entry = float(frame["close"].iloc[start])
        exit_ = float(frame["close"].iloc[end])
        realized = exit_ / entry - 1.0
        signed_return = direction * realized
        outcomes.append({
            "market_asof": market_asof,
            "direction": "long" if direction > 0 else "bearish",
            "entry": entry,
            "exit_date": str(frame.index[end].date()),
            "exit": exit_,
            "realized_return": realized,
            "signed_return": signed_return,
            "correct": signed_return > 0,
        })

    n_matured = len(outcomes)
    hit_rate = (
        sum(bool(o["correct"]) for o in outcomes) / n_matured
        if n_matured else None
    )
    avg_signed = (
        sum(o["signed_return"] for o in outcomes) / n_matured
        if n_matured else None
    )
    return {
        "status": "sufficient sample" if n_matured >= min_sample else "insufficient sample",
        "minimum_sample": min_sample,
        "horizon_bars": horizon,
        "n_archived": len(unique),
        "n_directional": n_matured + pending,
        "n_matured": n_matured,
        "n_pending": pending,
        "n_abstained": abstained,
        "hit_rate": hit_rate,
        "avg_signed_return": avg_signed,
        "outcomes": outcomes,
    }


def build_snapshot(ticker: str, name: str | None = None, refresh: bool = False,
                   generated_at: datetime | None = None,
                   record_trade: bool = False) -> tuple[dict, pd.DataFrame]:
    refresh_result = tools.refresh_data(ticker) if refresh else {
        "ticker": ticker, "targets": {}, "refresh_skipped": True}
    packet = tools.compute_indicators(ticker, record_trade=record_trade)
    if packet.get("error"):
        raise RuntimeError(f"{ticker}: {packet['error']}")
    df = indicators.get_stock_data(ticker)
    if df is None or df.empty:
        raise RuntimeError(f"{ticker}: no market data")

    generated_at = generated_at or datetime.now(timezone.utc)
    market_asof = str(pd.Timestamp(df.index[-1]).date())
    snapshot = {
        "schema_version": 1,
        "ticker": ticker,
        "name": name or ticker,
        "generated_at": generated_at.astimezone(timezone.utc).isoformat(),
        "market_asof": market_asof,
        "refresh": refresh_result,
        "indicators": _clean_json(packet),
    }
    return snapshot, df


def _fmt(value, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{suffix}" if isinstance(value, (int, float)) else str(value)


def _level_rows(levels: list[dict]) -> str:
    if not levels:
        return "No confirmed swing-pivot zones on this side."
    return "\n".join(
        f"- {_fmt(level.get('price'))} ({level.get('touches', 0)} touches; "
        f"last {level.get('last_touch', 'n/a')}; "
        f"{_fmt(level.get('dist_pct'), suffix='%')} from price)"
        for level in levels
    )


def render_markdown(snapshot: dict) -> str:
    p = snapshot["indicators"]
    overview = p.get("overview", {})
    trend = p.get("trend", {})
    momentum = p.get("momentum", {})
    volatility = p.get("volatility", {})
    volume = p.get("volume", {})
    levels = p.get("levels", {})
    sr = p.get("support_resistance", {})
    fib = p.get("fibonacci", {})
    council = p.get("council", {})
    review = snapshot.get("seven_day_review", {})
    validation = snapshot.get("validation", {})

    refresh_targets = snapshot.get("refresh", {}).get("targets", {})
    if refresh_targets:
        refresh_ok = all(v.get("refresh_succeeded") for v in refresh_targets.values())
        refresh_note = "successful" if refresh_ok else "partial/failed; prior cache retained where needed"
    else:
        refresh_note = "skipped (pinned cache used)"

    lines = [
        f"# Daily Technical Report — {snapshot['name']} ({snapshot['ticker']})",
        "",
        f"- Generated: {snapshot['generated_at']}",
        f"- Latest daily market bar: {snapshot['market_asof']}",
        f"- Explicit data refresh: {refresh_note}",
        "- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.",
        "",
        "## 1. Stock overview",
        "",
        f"Price is **{_fmt(overview.get('current_price'))}**, versus a "
        f"{overview.get('period_start', 'n/a')}–{overview.get('period_end', 'n/a')} "
        f"range of {_fmt(overview.get('period_low'))}–{_fmt(overview.get('period_high'))}. "
        f"It is {_fmt(overview.get('pct_from_high'), suffix='%')} from the period high "
        f"and {_fmt(overview.get('pct_from_low'), suffix='%')} from the period low.",
        "",
        "## 2. Trend analysis",
        "",
        f"- SMA20 / SMA50 / SMA200: {_fmt(trend.get('sma20'))} / "
        f"{_fmt(trend.get('sma50'))} / {_fmt(trend.get('sma200'))}.",
        f"- Price position: SMA20 **{trend.get('price_vs_sma20', 'n/a')}**, "
        f"SMA50 **{trend.get('price_vs_sma50', 'n/a')}**, "
        f"SMA200 **{trend.get('price_vs_sma200', 'n/a')}**.",
        f"- EMA20 / EMA50: {_fmt(trend.get('ema20'))} / {_fmt(trend.get('ema50'))}; "
        f"stack **{trend.get('ema_stack', 'n/a')}**.",
        f"- Latest SMA50/200 event: {trend.get('sma50_200_cross') or 'none'} "
        f"({trend.get('cross_date') or 'n/a'}).",
        "",
        "## 3. Momentum",
        "",
        f"- RSI(14): **{_fmt(momentum.get('rsi'))}** "
        f"({momentum.get('rsi_zone', 'n/a')}); divergence "
        f"**{momentum.get('rsi_divergence', 'n/a')}**.",
        f"- MACD / signal / histogram: {_fmt(momentum.get('macd'), 4)} / "
        f"{_fmt(momentum.get('macd_signal'), 4)} / "
        f"{_fmt(momentum.get('macd_hist'), 4)}.",
        f"- MACD state: **{momentum.get('macd_cross', 'n/a')}**, histogram "
        f"**{momentum.get('macd_hist_trend', 'n/a')}**.",
        "",
        "## 4. Volatility",
        "",
        f"- Bollinger lower / mid / upper: {_fmt(volatility.get('bb_lower'))} / "
        f"{_fmt(volatility.get('bb_mid'))} / {_fmt(volatility.get('bb_upper'))}; "
        f"%B {_fmt(volatility.get('percent_b'), 3)}.",
        f"- Squeeze: **{volatility.get('bb_squeeze', 'n/a')}**; volatility "
        f"**{volatility.get('volatility_direction', 'n/a')}**.",
        f"- ATR(14): {_fmt(volatility.get('atr'), 4)} "
        f"({_fmt(volatility.get('atr_pct'), suffix='%')} of price); expected daily "
        f"range {_fmt(volatility.get('expected_daily_range'))}.",
        "",
        "## 5. Volume",
        "",
    ]
    if not volume.get("available", False):
        lines.append("Volume analysis is unavailable for this asset.")
    else:
        lines.extend([
            f"- OBV trend **{volume.get('obv_trend', 'n/a')}**, strength "
            f"**{volume.get('obv_strength', 'n/a')}**.",
            f"- Price confirmation: **{volume.get('price_confirmation', 'n/a')}**; "
            f"divergence **{volume.get('divergence', 'n/a')}**.",
        ])

    lines.extend([
        "",
        "## 6. Key levels",
        "",
        f"- Quick 60-bar support / resistance: {_fmt(levels.get('support'))} / "
        f"{_fmt(levels.get('resistance'))}.",
        f"- Distance to support / resistance: "
        f"{_fmt(levels.get('dist_to_support_pct'), suffix='%')} / "
        f"{_fmt(levels.get('dist_to_resistance_pct'), suffix='%')}; "
        f"range reward:risk {_fmt(levels.get('risk_reward'))}.",
        "",
        "**Confirmed supports**",
        "",
        _level_rows(sr.get("supports", []) if sr.get("available") else []),
        "",
        "**Confirmed resistances**",
        "",
        _level_rows(sr.get("resistances", []) if sr.get("available") else []),
    ])
    if fib.get("available"):
        swing = fib.get("swing", {})
        nearest = fib.get("nearest_level", {})
        if swing.get("direction") == "down":
            swing_path = (
                f"{_fmt(swing.get('high'))} ({swing.get('high_date', 'n/a')}) "
                f"to {_fmt(swing.get('low'))} ({swing.get('low_date', 'n/a')})"
            )
        else:
            swing_path = (
                f"{_fmt(swing.get('low'))} ({swing.get('low_date', 'n/a')}) "
                f"to {_fmt(swing.get('high'))} ({swing.get('high_date', 'n/a')})"
            )
        lines.extend([
            "",
            f"Dominant swing: **{swing.get('direction', 'n/a')}**, "
            f"{swing_path}. "
            f"Nearest Fibonacci level is {nearest.get('ratio', 'n/a')} at "
            f"{_fmt(nearest.get('price'))} "
            f"({_fmt(nearest.get('dist_pct'), suffix='%')} from price).",
        ])
    else:
        lines.extend(["", "No clean dominant swing was available for Fibonacci levels."])

    if "cross_market" in p:
        lines.extend([
            "",
            "**Cross-market context (descriptive only)**",
            "",
            f"`{json.dumps(p['cross_market'], sort_keys=True)}`",
        ])

    direction = council.get("direction", "unavailable")
    if council.get("long_only_suppressed"):
        direction = "flat position; bearish evidence suppressed by long-only policy"
    lines.extend([
        "",
        "## 7. Indicator conflicts and risks",
        "",
        f"- Trend stack is **{trend.get('ema_stack', 'n/a')}** while MACD is "
        f"**{momentum.get('macd_cross', 'n/a')}**; disagreement here is a live "
        "trend/momentum conflict, not something to smooth over.",
        f"- RSI divergence is **{momentum.get('rsi_divergence', 'n/a')}** and "
        f"price/OBV confirmation is **{volume.get('price_confirmation', 'n/a')}**.",
        f"- Bollinger squeeze is **{volatility.get('bb_squeeze', 'n/a')}** while "
        f"ATR-based volatility is **{volatility.get('volatility_direction', 'n/a')}**.",
        "- Circle has a comparatively short public-market history; long-horizon "
        "statistics and any validation score require extra caution.",
        "",
        "## 8. Mechanical summary and bias",
        "",
        f"The council state is **{direction}**, conviction "
        f"**{_fmt(council.get('conviction'), 3)}**, effective breadth "
        f"**{_fmt(council.get('effective_breadth'))}**, and veto "
        f"**{council.get('veto', 'n/a')}**. The council is the only validated "
        "directional verdict; the classic indicators above remain descriptive.",
        "",
        "```json",
        json.dumps({
            "direction": council.get("direction"),
            "conviction": council.get("conviction"),
            "effective_breadth": council.get("effective_breadth"),
            "entry": council.get("entry"),
            "stop": council.get("stop"),
            "target": council.get("target"),
            "long_only_suppressed": council.get("long_only_suppressed"),
        }, indent=2),
        "```",
        "",
        "## 9. Seven-day report review",
        "",
    ])
    if review.get("prior_reports_found", 0) == 0:
        lines.append(
            "No prior report was found inside the seven-day window. This is the "
            "baseline; comparisons will populate automatically on later runs.")
    else:
        lines.extend([
            f"Compared with **{review['prior_reports_found']}** prior report(s) "
            f"from {review['window_start']} through {review['window_end']}, price "
            f"changed **{_fmt(review.get('price_change_pct'), suffix='%')}**. RSI "
            f"ranged from {_fmt(review.get('rsi_min'))} to "
            f"{_fmt(review.get('rsi_max'))}. Council state changed "
            f"{len(review.get('council_transitions', []))} time(s).",
            "",
            "| market date | price | RSI | EMA stack | MACD | council | conviction |",
            "|---|---:|---:|---|---|---|---:|",
        ])
        for row in review.get("rows", []):
            lines.append(
                f"| {row['market_asof']} | {_fmt(row.get('price'))} | "
                f"{_fmt(row.get('rsi'))} | {row.get('ema_stack', 'n/a')} | "
                f"{row.get('macd_cross', 'n/a')} | "
                f"{row.get('council_state', 'n/a')} | "
                f"{_fmt(row.get('conviction'), 3)} |")

    lines.extend([
        "",
        "## 10. Backtesting and validation",
        "",
        f"Archived-signal scorecard: **{validation.get('status', 'unavailable')}**. "
        f"At a {validation.get('horizon_bars', DEFAULT_VALIDATION_HORIZON)}-bar "
        f"horizon, {validation.get('n_matured', 0)} directional report(s) have "
        f"matured, {validation.get('n_pending', 0)} are pending, and "
        f"{validation.get('n_abstained', 0)} were honest abstentions.",
    ])
    if validation.get("n_matured", 0):
        lines.append(
            f"Observed directional hit rate is "
            f"{_fmt(100 * validation['hit_rate'], suffix='%')} and mean signed "
            f"forward return is "
            f"{_fmt(100 * validation['avg_signed_return'], suffix='%')}.")
    lines.extend([
        f"No performance claim is made until at least "
        f"{validation.get('minimum_sample', MIN_VALIDATION_SAMPLE)} directional "
        "reports mature. This is prospective validation of archived calls—not a "
        "replacement for a cost-aware portfolio backtest with slippage, turnover, "
        "and benchmark comparison.",
        "",
    ])
    return "\n".join(lines)


def save_report(snapshot: dict, markdown: str, output_dir: Path) -> dict:
    root = output_dir / _safe_ticker(snapshot["ticker"])
    stem = snapshot["market_asof"]
    json_text = json.dumps(_clean_json(snapshot), indent=2, allow_nan=False) + "\n"
    dated_json = root / f"{stem}.json"
    dated_md = root / f"{stem}.md"
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    for path, content in (
        (dated_json, json_text), (dated_md, markdown),
        (latest_json, json_text), (latest_md, markdown),
    ):
        _atomic_write(path, content)
    return {
        "dated_json": str(dated_json), "dated_markdown": str(dated_md),
        "latest_json": str(latest_json), "latest_markdown": str(latest_md),
    }


def publish_feishu(webhook_url: str, snapshot: dict, markdown: str,
                   timeout: float = 15.0) -> None:
    """Send the report as a Feishu custom-bot interactive card."""
    payload = {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": (
                        f"Daily Technical Report — {snapshot['name']} "
                        f"({snapshot['ticker']})"
                    ),
                },
                "template": "blue",
            },
            "body": {
                "elements": [{"tag": "markdown", "content": markdown}],
            },
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url, data=body, headers={"Content-Type": "application/json"},
        method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        if response.status >= 300:
            raise RuntimeError(f"Feishu webhook returned HTTP {response.status}")
        raw = response.read()
    if raw:
        result = json.loads(raw.decode("utf-8"))
        code = result.get("code", result.get("StatusCode", 0))
        if code != 0:
            message = result.get("msg", result.get("StatusMessage", "unknown error"))
            raise RuntimeError(f"Feishu webhook rejected report: {message}")


def generate_one(ticker: str, name: str | None, output_dir: Path,
                 review_days: int = DEFAULT_REVIEW_DAYS,
                 validation_horizon: int = DEFAULT_VALIDATION_HORIZON,
                 refresh: bool = False, webhook_url: str | None = None,
                 generated_at: datetime | None = None,
                 record_trade: bool = False) -> dict:
    previous = load_archives(output_dir, ticker)
    snapshot, df = build_snapshot(
        ticker, name=name, refresh=refresh, generated_at=generated_at,
        record_trade=record_trade)
    snapshot["seven_day_review"] = review_recent(previous, snapshot, review_days)
    snapshot["validation"] = validate_archived_forecasts(
        previous + [snapshot], df, horizon=validation_horizon)
    markdown = render_markdown(snapshot)
    paths = save_report(snapshot, markdown, output_dir)
    if webhook_url:
        publish_feishu(webhook_url, snapshot, markdown)
    return {
        "ticker": ticker, "market_asof": snapshot["market_asof"],
        "paths": paths, "published": bool(webhook_url),
        "validation_status": snapshot["validation"]["status"],
    }


def _assets(config_data: dict, tickers: list[str]) -> list[dict]:
    configured = {
        item["ticker"].upper(): item for item in config_data.get("assets", [])
    }
    if not tickers:
        return list(configured.values())
    return [
        configured.get(t.upper(), {"ticker": t.upper(), "name": t.upper()})
        for t in tickers
    ]


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="*", help="override configured assets")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--refresh", action="store_true",
                        help="explicitly refresh price caches before analysis")
    parser.add_argument("--record-trade", action="store_true",
                        help="allow an actionable report to append to the trade log")
    parser.add_argument("--publish-feishu", action="store_true",
                        help="publish through FEISHU_WEBHOOK_URL after saving")
    args = parser.parse_args(argv)

    config_data = load_config(args.config)
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL") if args.publish_feishu else None
    if args.publish_feishu and not webhook_url:
        raise SystemExit("--publish-feishu requires FEISHU_WEBHOOK_URL")

    results = []
    for asset in _assets(config_data, args.tickers):
        results.append(generate_one(
            ticker=asset["ticker"], name=asset.get("name"),
            output_dir=args.output_dir,
            review_days=int(config_data.get("review_days", DEFAULT_REVIEW_DAYS)),
            validation_horizon=int(config_data.get(
                "validation_horizon", DEFAULT_VALIDATION_HORIZON)),
            refresh=args.refresh, webhook_url=webhook_url,
            record_trade=args.record_trade,
        ))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
