import json
import tools


def test_compute_indicators_bundles_suite_and_council():
    out = tools.compute_indicators("BTC-USD")     # cached
    assert out["ticker"] == "BTC-USD"
    for section in ("overview", "trend", "momentum", "volatility", "volume", "levels", "council"):
        assert section in out
    assert out["council"]["available"] is True
    assert out["council"]["direction"] in ("long", "short", "flat")


def test_get_stock_data_returns_rows():
    out = tools.get_stock_data("BTC-USD", 30)
    assert out["ticker"] == "BTC-USD" and out["n_rows"] == 30
    r = out["rows"][0]
    assert set(r) == {"date", "open", "high", "low", "close", "volume"}


def test_output_is_strict_json_no_nan():
    out = tools._clean(tools.compute_indicators("BTC-USD"))
    json.dumps(out, allow_nan=False, default=str)     # must not raise on NaN/Inf


def test_council_only():
    v = tools.council_verdict("BTC-USD")
    assert v["available"] is True
    assert "effective_breadth" in v and "conviction" in v
