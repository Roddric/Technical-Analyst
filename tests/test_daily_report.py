from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

import daily_report as dr


def _packet(price=100.0, rsi=50.0, direction="flat", conviction=0.0,
            suppressed=False):
    return {
        "ticker": "CRCL",
        "overview": {
            "current_price": price, "period_start": "2026-01-01",
            "period_end": "2026-07-10", "period_high": 120.0,
            "period_low": 80.0, "pct_from_high": -16.67,
            "pct_from_low": 25.0,
        },
        "trend": {
            "sma20": 98.0, "sma50": 95.0, "sma200": 90.0,
            "price_vs_sma20": "above", "price_vs_sma50": "above",
            "price_vs_sma200": "above", "ema20": 99.0, "ema50": 96.0,
            "ema_stack": "bullish", "sma50_200_cross": "golden_cross",
            "cross_date": "2026-06-01",
        },
        "momentum": {
            "rsi": rsi, "rsi_zone": "neutral", "rsi_divergence": "none",
            "macd": 1.0, "macd_signal": 0.8, "macd_hist": 0.2,
            "macd_cross": "bullish", "macd_hist_trend": "expanding",
        },
        "volatility": {
            "bb_lower": 90.0, "bb_mid": 100.0, "bb_upper": 110.0,
            "percent_b": 0.5, "bb_squeeze": False, "atr": 3.0,
            "atr_pct": 3.0, "expected_daily_range": 3.0,
            "volatility_direction": "expanding",
        },
        "volume": {
            "available": True, "obv_trend": "rising", "obv_strength": "moderate",
            "price_confirmation": True, "divergence": "none",
        },
        "levels": {
            "support": 90.0, "resistance": 110.0,
            "dist_to_support_pct": 10.0, "dist_to_resistance_pct": 10.0,
            "risk_reward": 1.0,
        },
        "support_resistance": {
            "available": True,
            "supports": [{"price": 95.0, "touches": 2,
                          "last_touch": "2026-07-01", "dist_pct": -5.0}],
            "resistances": [{"price": 108.0, "touches": 3,
                             "last_touch": "2026-07-03", "dist_pct": 8.0}],
        },
        "fibonacci": {
            "available": True,
            "swing": {"direction": "up", "low": 80.0, "low_date": "2026-01-01",
                      "high": 120.0, "high_date": "2026-06-01"},
            "nearest_level": {"ratio": 0.5, "price": 100.0, "dist_pct": 0.0},
        },
        "council": {
            "available": True, "direction": direction, "conviction": conviction,
            "effective_breadth": 1.4, "veto": direction == "flat",
            "long_only_suppressed": suppressed,
            "entry": price, "stop": price if direction == "flat" else price - 5,
            "target": price if direction == "flat" else price + 10,
            "set_contributions": {},
        },
        "logged": False,
    }


def _snapshot(day, price=100.0, rsi=50.0, direction="flat", conviction=0.0,
              suppressed=False):
    return {
        "schema_version": 1, "ticker": "CRCL", "name": "Circle Internet Group",
        "generated_at": f"{day}T22:30:00+00:00", "market_asof": day,
        "refresh": {"targets": {}},
        "indicators": _packet(price, rsi, direction, conviction, suppressed),
    }


def _market_frame(n=20):
    idx = pd.bdate_range("2026-07-01", periods=n)
    close = np.arange(n, dtype=float) + 100.0
    return pd.DataFrame({
        "open": close, "high": close + 1, "low": close - 1,
        "close": close, "volume": 1000.0,
    }, index=idx)


def test_review_recent_uses_prior_seven_calendar_days():
    previous = [
        _snapshot("2026-07-01", 90, 40),
        _snapshot("2026-07-05", 95, 45, "long", 0.4),
        _snapshot("2026-07-09", 98, 48, "long", 0.5),
    ]
    current = _snapshot("2026-07-10", 100, 50, "flat", 0.0)

    review = dr.review_recent(previous, current, review_days=7)

    assert review["prior_reports_found"] == 2
    assert round(review["price_change_pct"], 2) == 5.26
    assert len(review["council_transitions"]) == 1
    assert review["rows"][0]["market_asof"] == "2026-07-05"


def test_validation_scores_matured_and_keeps_flat_as_abstention():
    df = _market_frame()
    first = str(df.index[0].date())
    second = str(df.index[1].date())
    recent = str(df.index[-2].date())
    snapshots = [
        _snapshot(first, direction="long", conviction=0.5),
        _snapshot(second, direction="flat"),
        _snapshot(recent, direction="long", conviction=0.5),
    ]

    result = dr.validate_archived_forecasts(snapshots, df, horizon=5)

    assert result["n_matured"] == 1
    assert result["hit_rate"] == 1.0
    assert result["n_pending"] == 1
    assert result["n_abstained"] == 1
    assert result["status"] == "insufficient sample"


def test_long_only_suppressed_is_scored_as_bearish():
    df = _market_frame()
    df["close"] = np.arange(len(df), 0, -1, dtype=float) + 100
    day = str(df.index[0].date())
    snapshot = _snapshot(day, direction="flat", suppressed=True)

    result = dr.validate_archived_forecasts([snapshot], df, horizon=5)

    assert result["n_matured"] == 1
    assert result["outcomes"][0]["direction"] == "bearish"
    assert result["outcomes"][0]["correct"] is True


def test_render_includes_review_and_validation_sections():
    snapshot = _snapshot("2026-07-10")
    snapshot["seven_day_review"] = dr.review_recent([], snapshot)
    snapshot["validation"] = dr.validate_archived_forecasts(
        [snapshot], _market_frame(), horizon=5)

    markdown = dr.render_markdown(snapshot)

    assert "Daily Technical Report" in markdown
    assert "## 9. Seven-day report review" in markdown
    assert "## 10. Backtesting and validation" in markdown
    assert "insufficient sample" in markdown
    assert "not tick-level real-time" in markdown


def test_save_and_load_archives(tmp_path):
    snapshot = _snapshot("2026-07-10")
    snapshot["seven_day_review"] = dr.review_recent([], snapshot)
    snapshot["validation"] = dr.validate_archived_forecasts([], _market_frame())
    markdown = dr.render_markdown(snapshot)

    paths = dr.save_report(snapshot, markdown, tmp_path)
    loaded = dr.load_archives(tmp_path, "CRCL")

    assert len(loaded) == 1
    assert loaded[0]["market_asof"] == "2026-07-10"
    assert json.loads(
        Path(paths["latest_json"]).read_text(encoding="utf-8")
    )["ticker"] == "CRCL"


def test_build_snapshot_refreshes_and_uses_latest_bar(monkeypatch):
    df = _market_frame()
    monkeypatch.setattr(
        dr.tools, "refresh_data",
        lambda ticker: {"ticker": ticker, "targets": {
            ticker: {"refresh_succeeded": True, "rows": len(df),
                     "market_asof": str(df.index[-1].date())}}})
    monkeypatch.setattr(
        dr.tools, "compute_indicators",
        lambda ticker, record_trade=True: _packet())
    monkeypatch.setattr(dr.indicators, "get_stock_data", lambda ticker: df)

    snapshot, returned = dr.build_snapshot(
        "CRCL", "Circle Internet Group", refresh=True,
        generated_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        record_trade=False)

    assert snapshot["market_asof"] == str(df.index[-1].date())
    assert snapshot["refresh"]["targets"]["CRCL"]["refresh_succeeded"] is True
    assert returned is df


def test_publish_feishu_sends_interactive_card(monkeypatch):
    snapshot = _snapshot("2026-07-10")
    seen = {}

    class Response:
        status = 200

        def read(self):
            return b'{"code": 0}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout):
        seen["payload"] = json.loads(req.data)
        seen["timeout"] = timeout
        return Response()

    monkeypatch.setattr(dr.request, "urlopen", fake_urlopen)
    dr.publish_feishu("https://example.invalid/hook", snapshot, "# report")

    assert seen["payload"]["msg_type"] == "interactive"
    assert seen["payload"]["card"]["body"]["elements"][0]["content"] == "# report"
