import arbiter, risk, plan
from regime import Regime


def test_assemble_roundtrips_to_dict():
    reg = Regime("bull", {"adx": 25.0})
    dec = arbiter.Decision(1, 0.7, {"Fast": 0.5}, 1.0)
    lv = risk.Levels(100.0, 96.0, 108.0, 0.001, False, "rule")
    p = plan.assemble_plan("BTC-USD", reg, dec, lv, {"max_abs_corr": 0.3, "ok": True})
    d = p.to_dict()
    assert d["asset"] == "BTC-USD" and d["direction"] == 1
    assert d["regime_label"] == "bull" and d["entry"] == 100.0
    assert d["set_contributions"] == {"Fast": 0.5}
