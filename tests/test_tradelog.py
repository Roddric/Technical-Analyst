import numpy as np
import pandas as pd
import pytest

import tradelog


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "trade_log.jsonl"


def _plan(direction="long", entry=100.0, stop=96.0, target=108.0, veto=False, available=True):
    return {"available": available, "direction": direction, "veto": veto,
            "entry": entry, "stop": stop, "target": target,
            "size_fraction": 0.01, "conviction": 0.6, "effective_breadth": 2.0}


def _bars(dates, highs, lows, closes):
    idx = pd.to_datetime(dates)
    return pd.DataFrame({"high": highs, "low": lows, "close": closes,
                         "open": closes, "volume": 1.0}, index=idx)


def test_records_actionable_only(log_path):
    assert tradelog.record_plan("AAA", _plan("long"), "2024-01-10", path=log_path) is True
    assert tradelog.record_plan("BBB", _plan("flat"), "2024-01-10", path=log_path) is False  # not actionable
    assert tradelog.record_plan("CCC", _plan(veto=True), "2024-01-10", path=log_path) is False
    tickers = [r["ticker"] for r in tradelog._load_all(log_path)]
    assert tickers == ["AAA"]


def test_one_open_plan_per_ticker(log_path):
    assert tradelog.record_plan("AAA", _plan(), "2024-01-10", path=log_path) is True
    assert tradelog.record_plan("AAA", _plan(), "2024-01-11", path=log_path) is False  # already open
    assert len(tradelog._load_all(log_path)) == 1


def test_target_hit_is_win(log_path):
    tradelog.record_plan("AAA", _plan("long", 100, 96, 108), "2024-01-10", path=log_path)
    bars = _bars(["2024-01-11", "2024-01-12"], highs=[103, 109], lows=[99, 104], closes=[102, 108])
    tradelog.update_open_plans(path=log_path, loader=lambda t: bars)
    r = tradelog._load_all(log_path)[0]
    assert r["status"] == "win" and r["exit_price"] == 108 and round(r["realized_R"], 2) == 2.0


def test_stop_hit_is_loss(log_path):
    tradelog.record_plan("AAA", _plan("long", 100, 96, 108), "2024-01-10", path=log_path)
    bars = _bars(["2024-01-11"], highs=[101], lows=[95], closes=[97])   # low pierces stop
    tradelog.update_open_plans(path=log_path, loader=lambda t: bars)
    r = tradelog._load_all(log_path)[0]
    assert r["status"] == "loss" and round(r["realized_R"], 2) == -1.0


def test_same_bar_tie_is_loss(log_path):
    tradelog.record_plan("AAA", _plan("long", 100, 96, 108), "2024-01-10", path=log_path)
    bars = _bars(["2024-01-11"], highs=[108], lows=[96], closes=[100])  # spans both
    tradelog.update_open_plans(path=log_path, loader=lambda t: bars)
    assert tradelog._load_all(log_path)[0]["status"] == "loss"


def test_open_plan_marks_to_market(log_path):
    tradelog.record_plan("AAA", _plan("long", 100, 96, 108), "2024-01-10", path=log_path)
    bars = _bars(["2024-01-11"], highs=[103], lows=[99], closes=[102])  # neither hit
    summary = tradelog.update_open_plans(path=log_path, loader=lambda t: bars)
    r = tradelog._load_all(log_path)[0]
    assert r["status"] == "open"
    assert round(r["unrealized_return"], 4) == 0.02          # (102-100)/100
    assert summary["n_open"] == 1 and summary["n_closed"] == 0


def test_short_target_and_summary(log_path):
    tradelog.record_plan("SHT", _plan("short", 100, 104, 92), "2024-01-10", path=log_path)
    bars = _bars(["2024-01-11"], highs=[101], lows=[91], closes=[93])   # low hits short target 92
    summary = tradelog.update_open_plans(path=log_path, loader=lambda t: bars)
    r = tradelog._load_all(log_path)[0]
    assert r["status"] == "win" and round(r["realized_R"], 2) == 2.0
    assert summary["win_rate"] == 1.0
    md = tradelog.render_markdown(summary)
    assert "trade log" in md and "SHT" in md
