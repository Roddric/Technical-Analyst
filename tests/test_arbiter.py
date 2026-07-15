import arbiter


def test_agreeing_sets_give_directional_call():
    d = arbiter.arbitrate({"Fast": 1.5, "Slow": 1.0}, {"Fast": 0.6, "Slow": 0.4})
    assert d.direction == 1
    assert 0.0 < d.conviction <= 1.0


def test_no_weight_means_flat():
    d = arbiter.arbitrate({"Fast": 2.0}, {})
    assert d.direction == 0 and d.conviction == 0.0
    assert d.effective_n == 0.0


def test_effective_n_flags_domination():
    balanced = arbiter.arbitrate({"a": 1.0, "b": 1.0}, {"a": 0.5, "b": 0.5})
    dominated = arbiter.arbitrate({"a": 1.0, "b": 1.0}, {"a": 0.95, "b": 0.05})
    assert abs(balanced.effective_n - 2.0) < 1e-9
    assert dominated.effective_n < 1.5


def test_is_deterministic():
    a = arbiter.arbitrate({"Fast": 0.8, "Slow": -0.9}, {"Fast": 0.5, "Slow": 0.5})
    b = arbiter.arbitrate({"Fast": 0.8, "Slow": -0.9}, {"Fast": 0.5, "Slow": 0.5})
    assert a == b
