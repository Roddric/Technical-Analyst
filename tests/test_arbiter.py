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


def test_long_only_suppresses_short():
    d = arbiter.arbitrate({"Fast": -1.5, "Slow": -1.0}, {"Fast": 0.6, "Slow": 0.4},
                          long_only=True)
    assert d.direction == 0
    assert d.conviction == 0.0
    assert d.long_only_suppressed is True
    assert d.effective_n > 0             # evidence preserved, not a no-signal flat


def test_long_only_keeps_long():
    d = arbiter.arbitrate({"Fast": 1.5, "Slow": 1.0}, {"Fast": 0.6, "Slow": 0.4},
                          long_only=True)
    assert d.direction == 1 and d.long_only_suppressed is False


def test_default_still_allows_short():
    d = arbiter.arbitrate({"Fast": -1.5, "Slow": -1.0}, {"Fast": 0.6, "Slow": 0.4})
    assert d.direction == -1 and d.long_only_suppressed is False


def test_nan_score_never_emits_short_or_nan_conviction():
    # A degenerate NaN weighted score must resolve to a clean flat — never a short
    # (which would violate long-only) and never a NaN conviction leaking downstream.
    for long_only in (False, True):
        d = arbiter.arbitrate({"Fast": float("nan")}, {"Fast": 1.0}, long_only=long_only)
        assert d.direction == 0
        assert d.conviction == 0.0
        assert d.long_only_suppressed is False
