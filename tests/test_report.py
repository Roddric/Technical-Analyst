import plan as plan_mod
import report
import run


def _sample_plan(veto=False):
    return plan_mod.Plan(
        asset="AAPL", regime_label="bull", direction=1, conviction=0.62,
        entry=100.0, stop=96.0, target=108.0, size=0.0012,
        veto=veto, reason="ATR=1.0, 2.0x stop, 2.0R target",
        effective_n=1.2, set_contributions={"Set1": 0.5, "Set2": -0.1},
        decorrelation={"max_abs_corr": 0.44, "ok": True})


def test_render_contains_verdict_and_levels():
    md = report.render_markdown(_sample_plan())
    assert "# Indicator Council — AAPL" in md
    assert "LONG" in md and "0.62" in md
    assert "entry" in md and "100.0000" in md
    assert "Effective breadth" in md and "single bet" in md.lower()  # eff_n<1.5 note


def test_render_veto_hides_levels():
    md = report.render_markdown(_sample_plan(veto=True))
    assert "VETO" in md
    assert "reward:risk" not in md


def test_write_report_creates_file(tmp_path):
    p = _sample_plan()
    path = report.write_report(p, tmp_path)
    assert path.exists() and path.name == "AAPL.md"
    assert "AAPL" in path.read_text(encoding="utf-8")


def test_analyze_ticker_on_cached_asset():
    # BTC-USD is in the cache; exercises the on-demand single-ticker path offline.
    p = run.analyze_ticker("BTC-USD")
    assert p is not None and p.asset == "BTC-USD"
    assert p.direction in (-1, 0, 1)


def test_safe_return_mode_defaults_for_unknown():
    assert run._safe_return_mode("SOME_UNLISTED_TICKER") == "log"
