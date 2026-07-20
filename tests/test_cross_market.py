import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

import cross_market


def _frame(dates, closes):
    """OHLCV frame with flat OHLC = close, on the given dates."""
    closes = np.asarray(closes, dtype=float)
    idx = pd.to_datetime(list(dates))
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes,
         "volume": np.ones(len(closes))},
        index=idx,
    )


def test_asof_strict_before_excludes_same_date():
    foreign = _frame(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
                     [10, 20, 30, 40])
    target = pd.to_datetime(["2021-01-02", "2021-01-03", "2021-01-04"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=True)
    # each target date maps to the PRIOR foreign date, never the same date
    assert list(aligned["close"].values) == [10.0, 20.0, 30.0]


def test_asof_allow_exact_uses_same_date():
    foreign = _frame(["2021-01-01", "2021-01-02", "2021-01-03"], [10, 20, 30])
    target = pd.to_datetime(["2021-01-02", "2021-01-03"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=False)
    assert list(aligned["close"].values) == [20.0, 30.0]


def test_asof_holiday_robust_and_no_future_leak():
    # foreign missing 2021-01-02; target 2021-01-03 falls back to 01-01
    foreign = _frame(["2021-01-01", "2021-01-04"], [10, 40])
    target = pd.to_datetime(["2021-01-03"])
    aligned = cross_market._asof_align(target, foreign[["close"]], strict_before=True)
    assert aligned["close"].iloc[0] == 10.0            # last before D, not the future 40


def test_causal_zscore_is_causal_and_correct():
    s = pd.Series(np.arange(1, 21, dtype=float))
    full = cross_market._causal_zscore(s, window=5)
    partial = cross_market._causal_zscore(s.iloc[:10], window=5)
    assert full.iloc[9] == pytest.approx(partial.iloc[9])   # future bars don't move it
    # manual check at index 9: window = values 6..10, mean 8, std(ddof=1)=1.5811, z=(10-8)/1.5811
    assert full.iloc[9] == pytest.approx((10 - 8) / np.std([6, 7, 8, 9, 10], ddof=1))


def test_causal_zscore_flat_series_is_nan_not_inf():
    s = pd.Series([5.0] * 10)
    z = cross_market._causal_zscore(s, window=5)
    assert not np.isinf(z).any()
    assert z.iloc[-1] != z.iloc[-1] or np.isnan(z.iloc[-1])   # NaN, not inf


def test_adr_overnight_signal_values_are_causal():
    # ADR returns: [nan, +0.10, +0.10, 0.0]. Strict-before alignment to targets
    # 01-03/01-04/01-05 -> [0.10, 0.10, 0.0]; causal z(window=2) -> [nan, nan, -0.7071].
    # A leaky (same-date) alignment would give [0.10, 0.0, 0.0] -> z [nan, -0.7071, nan],
    # so asserting the finite value lands at index 2 (not index 1) pins the causal guard
    # to the FUNCTION's own output.
    adr = _frame(["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"], [100, 110, 121, 121])
    target = _frame(["2021-01-03", "2021-01-04", "2021-01-05"], [1, 1, 1])
    sig = cross_market.adr_overnight_signal(target, adr, window=2)
    assert sig.name == "xmkt_adr_overnight"
    assert list(sig.index) == list(target.index)
    assert np.isnan(sig.iloc[0]) and np.isnan(sig.iloc[1])
    assert sig.iloc[2] == pytest.approx((0.0 - 0.05) / np.std([0.10, 0.0], ddof=1))


def test_adr_premium_snapshot_matches_hand_calc():
    # 152.31 * 1480 = 225418.8 ; / 228500 - 1 = -1.349% -> -1.35
    target = _frame(["2026-07-15", "2026-07-16"], [228500, 228500])
    adr = _frame(["2026-07-14", "2026-07-15"], [150.0, 152.31])
    fx = _frame(["2026-07-14", "2026-07-15"], [1480.0, 1480.0])
    snap = cross_market.adr_premium_snapshot(target, adr, fx, adr_ratio=1.0)
    assert snap["available"] is True
    assert snap["premium_pct"] == pytest.approx(-1.35, abs=0.01)
    assert snap["zone"] == "within_band"


def test_adr_premium_snapshot_zone_bands():
    target = _frame(["2026-01-01"], [100.0])
    adr_rich = _frame(["2026-01-01"], [110.0])          # +10% -> rich
    fx = _frame(["2026-01-01"], [1.0])
    assert cross_market.adr_premium_snapshot(target, adr_rich, fx, 1.0)["zone"] == "rich"
    adr_cheap = _frame(["2026-01-01"], [90.0])           # -10% -> cheap
    assert cross_market.adr_premium_snapshot(target, adr_cheap, fx, 1.0)["zone"] == "cheap"


def test_adr_premium_snapshot_missing_data_unavailable():
    target = _frame(["2026-01-01"], [100.0])
    empty = _frame([], [])
    snap = cross_market.adr_premium_snapshot(target, empty, empty, 1.0)
    assert snap["available"] is False


def test_adr_premium_signal_is_series_aligned_to_target():
    n = 80
    dates = pd.bdate_range("2021-01-01", periods=n)
    target = _frame(dates, np.linspace(200000, 230000, n))
    adr = _frame(dates, np.linspace(140, 155, n))
    fx = _frame(dates, np.full(n, 1480.0))
    # regime_start before the fixture so this exercises ALIGNMENT alone; the
    # regime gate itself is covered by the tests below.
    sig = cross_market.adr_premium_signal(target, adr, fx, adr_ratio=1.0, window=20,
                                          regime_start="2020-01-01")
    assert sig.name == "xmkt_adr_premium"
    assert list(sig.index) == list(target.index)
    assert np.isfinite(sig.iloc[-1])           # enough history -> finite tail


# Post-conversion by default: the premium signal only has a defined mean-reversion
# premise after ADR_TWO_WAY_CONVERSION_DATE, so build_signals fixtures live there.
def _long_legs(n=300, start="2026-08-03"):
    dates = pd.bdate_range(start, periods=n)
    target = _frame(dates, np.linspace(200000, 230000, n))
    adr = _frame(dates, np.linspace(140, 155, n))
    fx = _frame(dates, np.full(n, 1480.0))
    return target, adr, fx


def test_build_signals_returns_both_with_fake_loader():
    target, adr, fx = _long_legs()
    loader = lambda t: {"SKHY": adr, "KRW=X": fx}.get(t)
    sigs = cross_market.build_signals(target, "000660.KS", loader=loader)
    assert set(sigs) == {"xmkt_adr_overnight", "xmkt_adr_premium"}
    assert all(len(s) == len(target) for s in sigs.values())


def test_build_signals_unconfigured_asset_is_empty():
    target, _, _ = _long_legs()
    assert cross_market.build_signals(target, "AAPL", loader=lambda t: None) == {}


def test_build_signals_missing_leg_is_empty():
    target, _, _ = _long_legs()
    assert cross_market.build_signals(target, "000660.KS", loader=lambda t: None) == {}


def test_build_signals_short_history_is_empty():
    target, adr, fx = _long_legs(n=50)          # < XMKT_MIN_HISTORY
    loader = lambda t: {"SKHY": adr, "KRW=X": fx}.get(t)
    assert cross_market.build_signals(target, "000660.KS", loader=loader) == {}


def test_run_analyze_asset_appends_cross_market_signals(monkeypatch, synth_ohlcv):
    import run
    df = synth_ohlcv(n=300, seed=3)
    seen = {}

    def fake_build(target_df, asset, loader=None):
        seen["asset"] = asset
        seen["is_df"] = target_df is df
        return {}                       # empty -> no behavior change, just verify wiring

    monkeypatch.setattr(run.cross_market_mod, "build_signals", fake_build)
    run.analyze_asset(df, "000660.KS")
    assert seen["asset"] == "000660.KS" and seen["is_df"] is True


def test_compute_indicators_adds_cross_market_snapshot(monkeypatch):
    import json
    import tools
    import cross_market as cm

    target, adr, fx = _long_legs()
    # make the descriptive fetch return our synthetic legs, and the local df
    monkeypatch.setattr(tools.ind, "get_stock_data",
                        lambda t, *a, **k: {"SKHY": adr, "KRW=X": fx,
                                            "000660.KS": target}.get(t))
    # keep the indicator suite itself from doing heavy work: stub compute_indicators core
    monkeypatch.setattr(tools.ind, "compute_indicators", lambda df: {"overview": {}})
    monkeypatch.setattr(tools, "council_verdict", lambda t: {"available": False})
    monkeypatch.setattr(tools.tradelog, "record_plan", lambda *a, **k: False)

    out = tools.compute_indicators("000660.KS")
    assert "cross_market" in out
    assert out["cross_market"]["available"] is True
    json.dumps(tools._clean(out), allow_nan=False)          # strict-JSON clean


def test_adr_premium_snapshot_real_ratio_is_ten():
    # SEC prospectus: 10 SKHY ADRs = 1 000660.KS share -> adr_ratio=10 (NOT 0.1).
    # 152.31 * 1480.47 * 10 / 1_842_000 - 1 = +22.4%.  0.1 would give -98.8%.
    local = _frame(["2026-07-16"], [1_842_000.0])
    adr = _frame(["2026-07-16"], [152.31])
    fx = _frame(["2026-07-16"], [1480.47])
    snap = cross_market.adr_premium_snapshot(local, adr, fx, adr_ratio=10.0)
    assert snap["premium_pct"] == pytest.approx(22.41, abs=0.05)
    assert snap["zone"] == "rich"


def test_adr_premium_snapshot_flags_conversion_regime():
    adr = _frame(["2026-07-16"], [152.31])
    fx = _frame(["2026-07-16"], [1480.47])
    pre = _frame(["2026-07-16"], [1_842_000.0])   # before 2026-07-29
    post = _frame(["2026-08-05"], [1_842_000.0])  # after 2026-07-29
    assert cross_market.adr_premium_snapshot(pre, adr, fx, 10.0)["arbitrage_regime"] == "scarcity_premium_one_way"
    assert cross_market.adr_premium_snapshot(post, adr, fx, 10.0)["arbitrage_regime"] == "two_way_active"


def test_asof_align_handles_mixed_datetime_resolution():
    # Real yfinance/CSV data mixes datetime64[s]/[us]/[ns]; merge_asof requires the
    # merge keys to match, so _asof_align must coerce both to one resolution.
    tgt = pd.DatetimeIndex(pd.to_datetime(["2021-01-02", "2021-01-03"])).astype("datetime64[s]")
    foreign = _frame(["2021-01-01", "2021-01-02"], [10, 20])
    foreign.index = foreign.index.astype("datetime64[us]")
    out = cross_market._asof_align(tgt, foreign[["close"]], strict_before=True)
    assert list(out["close"].values) == [10.0, 20.0]        # would MergeError before the fix


def test_build_signals_none_target_is_empty():
    assert cross_market.build_signals(None, "000660.KS", loader=lambda t: _frame(["2021-01-01"], [1])) == {}


# --- regime gate: the premium's reversion premise starts at two-way conversion ---

def _pre_post_legs(n_pre=40, n_post=40):
    """Legs straddling ADR_TWO_WAY_CONVERSION_DATE, with a deliberately different
    premium level on each side (~+50% pre, ~0% post) so any pre-regime value that
    leaked into a post-regime z-window would visibly move the result."""
    pre = pd.bdate_range("2026-05-01", periods=n_pre)      # before 2026-07-29
    post = pd.bdate_range("2026-08-03", periods=n_post)    # after
    dates = pre.append(post)
    target = _frame(dates, np.full(len(dates), 100_000.0))
    adr_px = np.concatenate([150_000 + np.arange(n_pre) * 10.0,      # ~+50% premium
                             100_000 + np.arange(n_post) * 10.0])    # ~0% premium
    adr = _frame(dates, adr_px)
    fx = _frame(dates, np.ones(len(dates)))
    return target, adr, fx


def test_adr_premium_signal_is_absent_before_conversion():
    target, adr, fx = _pre_post_legs()
    conv = pd.Timestamp(config.ADR_TWO_WAY_CONVERSION_DATE)
    sig = cross_market.adr_premium_signal(target, adr, fx, adr_ratio=1.0, window=5,
                                          regime_start=conv)
    assert list(sig.index) == list(target.index)          # still target-aligned
    assert sig[sig.index < conv].isna().all()             # one-way era: no signal at all
    assert np.isfinite(sig[sig.index >= conv]).any()      # post-conversion: emits


def test_adr_premium_zscore_excludes_pre_regime_history():
    """The load-bearing one: pre-conversion premium must never enter a
    post-conversion trailing mean/std. Dropping pre-regime bars makes the
    post-regime series identical to one computed from post-regime data alone;
    merely MASKING after z-scoring would not."""
    target, adr, fx = _pre_post_legs()
    conv = pd.Timestamp(config.ADR_TWO_WAY_CONVERSION_DATE)
    full = cross_market.adr_premium_signal(target, adr, fx, adr_ratio=1.0, window=5,
                                           regime_start=conv)
    post_only = cross_market.adr_premium_signal(
        target[target.index >= conv], adr, fx, adr_ratio=1.0, window=5,
        regime_start=conv)
    pd.testing.assert_series_equal(full[full.index >= conv], post_only)


def test_build_signals_drops_premium_when_regime_history_short():
    """Asymmetry: plenty of DATA history, but little REGIME history. The
    overnight signal (regime-independent) survives; the premium does not."""
    target, adr, fx = _long_legs(n=300, start="2026-01-01")   # conversion mid-sample
    loader = lambda t: {"SKHY": adr, "KRW=X": fx}.get(t)
    sigs = cross_market.build_signals(target, "000660.KS", loader=loader)
    assert "xmkt_adr_overnight" in sigs                       # clears XMKT_MIN_HISTORY
    assert "xmkt_adr_premium" not in sigs                     # fails XMKT_REGIME_MIN_BARS


# --- Phase B: 7709.HK leveraged-ETF divergence ---

def test_etf_divergence_math_is_exact():
    """divergence = etf_ret - leverage*anchor_ret, on same-date Korea returns."""
    dates = pd.bdate_range("2026-01-01", periods=6)
    und = _frame(dates, [100.0, 110.0, 121.0, 121.0, 121.0, 133.1])   # +10%,+10%,0,0,+10%
    etf = _frame(dates, [50.0, 60.0, 66.0, 66.0, 66.0, 79.2])         # +20%,+10%,0,0,+20%
    sig = cross_market.etf_divergence_signal(etf, und, None, leverage=2.0, window=2)
    assert sig.name == "xmkt_etf_divergence"
    assert list(sig.index) == list(etf.index)
    # bar 2: etf +10% vs 2*(+10%) = +20% expected -> divergence = -0.10 (under-reacting)
    # bar 5: etf +20% vs 2*(+10%) = +20% expected -> divergence =  0.00 (tracking)
    raw = etf["close"].pct_change() - 2.0 * und["close"].pct_change()
    assert raw.iloc[2] == pytest.approx(-0.10)
    assert raw.iloc[5] == pytest.approx(0.0, abs=1e-12)


def test_etf_anchor_uses_same_date_korea_return():
    """HK closes after Korea, so the SAME-date underlying return is causally
    available and must be used (not the prior day's)."""
    dates = pd.bdate_range("2026-01-01", periods=4)
    und = _frame(dates, [100.0, 110.0, 121.0, 133.1])       # +10% each day
    anchor = cross_market._etf_anchor_return(dates, und, None)
    assert np.isnan(anchor.iloc[0])                          # no prior bar
    assert anchor.iloc[1] == pytest.approx(0.10)             # same-date, not shifted


def test_etf_substitute_anchor_fires_only_on_korea_holidays():
    """The load-bearing coalesce: same-date Korea return where Korea traded;
    SKHY strictly-before overnight return only where it did not."""
    etf_dates = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"])
    # Korea is MISSING 2026-01-06 (holiday); trades 01-05 and 01-07
    und = _frame(["2026-01-02", "2026-01-05", "2026-01-07"], [100.0, 110.0, 121.0])
    # SKHY prints every day; its return into 01-06 is +50% (deliberately distinct)
    sub = _frame(["2026-01-04", "2026-01-05", "2026-01-06"], [10.0, 15.0, 30.0])
    anchor = cross_market._etf_anchor_return(etf_dates, und, sub)
    assert anchor.iloc[0] == pytest.approx(0.10)     # Korea traded 01-05: 100->110
    assert anchor.iloc[1] == pytest.approx(0.50)     # holiday -> SKHY strictly-before
    assert anchor.iloc[2] == pytest.approx(0.10)     # Korea traded 01-07: 110->121


def test_etf_divergence_snapshot_reads_over_and_under_reaction():
    dates = pd.bdate_range("2026-01-01", periods=3)
    und = _frame(dates, [100.0, 110.0, 121.0])               # +10% each day
    over = _frame(dates, [50.0, 60.0, 78.0])                 # last +30% vs +20% expected
    snap = cross_market.etf_divergence_snapshot(over, und, None, leverage=2.0)
    assert snap["available"] is True
    assert snap["anchor_return_pct"] == pytest.approx(10.0)
    assert snap["expected_return_pct"] == pytest.approx(20.0)
    assert snap["divergence_pct"] == pytest.approx(10.0)
    assert "over-reacting" in snap["read"]
    under = _frame(dates, [50.0, 60.0, 66.0])                # last +10% vs +20%
    assert "under-reacting" in cross_market.etf_divergence_snapshot(
        under, und, None, leverage=2.0)["read"]


def test_etf_divergence_snapshot_unavailable_on_thin_data():
    one = _frame(["2026-01-01"], [50.0])
    assert cross_market.etf_divergence_snapshot(one, one, None)["available"] is False


def _etf_legs(n=300, start="2025-01-01"):
    dates = pd.bdate_range(start, periods=n)
    und = _frame(dates, np.linspace(200000, 230000, n))
    etf = _frame(dates, np.linspace(40, 50, n))
    sub = _frame(dates, np.linspace(140, 155, n))
    return etf, und, sub


def test_build_signals_dispatches_etf_shape():
    etf, und, sub = _etf_legs()
    loader = lambda t: {"000660.KS": und, "SKHY": sub}.get(t)
    sigs = cross_market.build_signals(etf, "7709.HK", loader=loader)
    assert set(sigs) == {"xmkt_etf_divergence"}          # NOT the ADR signals
    assert len(sigs["xmkt_etf_divergence"]) == len(etf)


def test_build_signals_etf_missing_underlying_is_empty():
    etf, _, _ = _etf_legs()
    assert cross_market.build_signals(etf, "7709.HK", loader=lambda t: None) == {}


def test_build_signals_etf_short_history_is_empty():
    etf, und, sub = _etf_legs(n=50)                      # < XMKT_MIN_HISTORY
    loader = lambda t: {"000660.KS": und, "SKHY": sub}.get(t)
    assert cross_market.build_signals(etf, "7709.HK", loader=loader) == {}


def test_compute_indicators_dispatches_etf_snapshot(monkeypatch):
    """7709.HK routes to the ETF divergence snapshot, not the ADR premium."""
    import json
    import tools

    etf, und, sub = _etf_legs()
    monkeypatch.setattr(tools.ind, "get_stock_data",
                        lambda t, *a, **k: {"7709.HK": etf, "000660.KS": und,
                                            "SKHY": sub}.get(t))
    monkeypatch.setattr(tools.ind, "compute_indicators", lambda df: {"overview": {}})
    monkeypatch.setattr(tools, "council_verdict", lambda t: {"available": False})
    monkeypatch.setattr(tools.tradelog, "record_plan", lambda *a, **k: False)

    out = tools.compute_indicators("7709.HK")
    assert out["cross_market"]["available"] is True
    assert "read" in out["cross_market"]                  # ETF-shaped, not ADR-shaped
    assert "premium_pct" not in out["cross_market"]
    json.dumps(tools._clean(out), allow_nan=False)        # strict-JSON clean


def test_regime_start_is_per_pair_not_global():
    """Regression: a module-level regime default would gate a MATURE pair's
    entire history away and look identical to 'no edge found'. 2330.TW has
    regime_start=None, so its full history must survive even though SK Hynix's
    conversion date is still in the future."""
    assert config.CROSS_MARKET_MAP["2330.TW"]["regime_start"] is None
    assert config.CROSS_MARKET_MAP["000660.KS"]["regime_start"] == \
        config.ADR_TWO_WAY_CONVERSION_DATE

    # Sample sits entirely BEFORE SK Hynix's conversion date.
    target, adr, fx = _long_legs(n=300, start="2020-01-01")
    loader = lambda t: {"TSM": adr, "TWD=X": fx}.get(t)
    sigs = cross_market.build_signals(target, "2330.TW", loader=loader)
    assert "xmkt_adr_premium" in sigs                 # ungated pair -> emits
    assert np.isfinite(sigs["xmkt_adr_premium"].iloc[-1])

    # Same data under the gated pair emits nothing — proving the gate is what
    # differs, not the data.
    loader2 = lambda t: {"SKHY": adr, "KRW=X": fx}.get(t)
    assert "xmkt_adr_premium" not in cross_market.build_signals(
        target, "000660.KS", loader=loader2)


# --- multi-calendar gaps: the bug synthetic aligned fixtures could not catch ---

# Real 2025-2026 dates where 7709.HK traded and 000660.KS did not (Korea
# holidays), taken from live data. Gaps recur every ~6-8 weeks, which caps the
# longest unbroken calendar run below the 60-bar window.
KOREA_HOLIDAYS_HK_OPEN = ["2025-12-31", "2026-02-16", "2026-03-02",
                          "2026-05-05", "2026-06-03"]


def test_causal_zscore_rolls_on_observations_not_rows():
    """A single interior NaN must not blank the next `window` outputs."""
    s = pd.Series(np.arange(1, 31, dtype=float))
    s.iloc[10] = np.nan                       # one gap, mid-series
    z = cross_market._causal_zscore(s, window=5)
    assert np.isnan(z.iloc[10])               # the gap itself stays NaN
    # Row-position rolling would blank indices 11..14; observation rolling does not.
    assert np.isfinite(z.iloc[11])
    # value matches a z-score over the last 5 OBSERVED points (9,10,12,13 -> and 11 is idx10=NaN)
    obs = s.dropna()
    exp = (obs - obs.rolling(5).mean()) / obs.rolling(5).std()
    assert z.iloc[11] == pytest.approx(exp.loc[11])


def test_etf_divergence_survives_real_korea_holiday_gaps():
    """Regression for the real failure: with genuine Korea-holiday gaps the
    longest unbroken calendar run is < XMKT_Z_WINDOW, so row-position rolling
    produced ZERO finite values and build_signals returned {} — indistinguishable
    from 'not enough history yet'."""
    etf_idx = pd.bdate_range("2025-10-16", "2026-07-16")
    gaps = pd.to_datetime(KOREA_HOLIDAYS_HK_OPEN)
    kor_idx = etf_idx.difference(gaps)                 # Korea shut on those dates
    assert len(gaps.intersection(etf_idx)) == len(gaps)  # gaps really are HK bars

    rng = np.random.default_rng(0)
    etf = _frame(etf_idx, 40 * np.cumprod(1 + rng.normal(0, 0.02, len(etf_idx))))
    und = _frame(kor_idx, 200000 * np.cumprod(1 + rng.normal(0, 0.01, len(kor_idx))))

    anchor = cross_market._etf_anchor_return(etf_idx, und, None)
    assert anchor.isna().sum() >= len(gaps)            # gaps are genuinely NaN

    # longest unbroken run must be under the window, or the fixture is not
    # reproducing the real condition.
    finite = anchor.notna().to_numpy()
    best = run = 0
    for v in finite:
        run = run + 1 if v else 0
        best = max(best, run)
    assert best < config.XMKT_Z_WINDOW

    sig = cross_market.etf_divergence_signal(etf, und, None, leverage=2.0)
    assert sig.notna().sum() > 0                       # was 0 before the fix
    assert sig.notna().sum() >= len(etf_idx) - config.XMKT_Z_WINDOW - len(gaps) - 5


# --- substitute-anchor FX back-out (no real occurrence yet: SKHY postdates
# every Korea holiday in the sample, so this path is UNTESTED by live data) ---

def test_substitute_anchor_backs_fx_out_of_usd_return():
    """SKHY prints in USD; the anchor must be a KRW move. With fx = KRW per USD,
    (1+r_krw) = (1+r_usd)(1+r_fx). Hand-computable: r_usd=+10%, r_fx=+1%
    -> r_krw = 1.10*1.01 - 1 = 0.111 exactly."""
    etf_idx = pd.to_datetime(["2026-08-03", "2026-08-04", "2026-08-05"])
    # Korea shut on 08-04 (fabricated holiday); trades either side.
    und = _frame(["2026-08-03", "2026-08-05"], [200000.0, 202000.0])
    # SKHY's session on date D closes AFTER HK's, so the freshest SKHY return
    # available to an HK bar on 08-04 is the one dated 08-03 (strictly before).
    sub = _frame(["2026-08-02", "2026-08-03"], [100.0, 110.0])   # r_usd = +0.10
    fx = _frame(["2026-08-02", "2026-08-03"], [1400.0, 1414.0])  # r_fx  = +0.01

    anchor = cross_market._etf_anchor_return(etf_idx, und, sub, fx)
    assert anchor.iloc[1] == pytest.approx(1.10 * 1.01 - 1.0)      # 0.111
    # Positive control: without the FX leg the same path yields the RAW USD
    # return, which is the wrong number by exactly the FX move.
    raw = cross_market._etf_anchor_return(etf_idx, und, sub, None)
    assert raw.iloc[1] == pytest.approx(0.10)
    assert raw.iloc[1] != pytest.approx(anchor.iloc[1])


def test_substitute_fx_backout_handles_negative_fx_move():
    """A weakening KRW must reduce, not inflate, the implied KRW return."""
    etf_idx = pd.to_datetime(["2026-08-03", "2026-08-04"])
    und = _frame(["2026-08-03"], [200000.0])
    sub = _frame(["2026-08-02", "2026-08-03"], [100.0, 105.0])     # r_usd = +5%
    fx = _frame(["2026-08-02", "2026-08-03"], [1400.0, 1386.0])    # r_fx  = -1%
    anchor = cross_market._etf_anchor_return(etf_idx, und, sub, fx)
    assert anchor.iloc[1] == pytest.approx(1.05 * 0.99 - 1.0)      # 0.0395


def test_substitute_fx_absent_falls_back_to_raw_usd_return():
    """substitute_fx is optional; without it behaviour is unchanged (raw USD)."""
    etf_idx = pd.to_datetime(["2026-08-03", "2026-08-04"])
    und = _frame(["2026-08-03"], [200000.0])
    sub = _frame(["2026-08-02", "2026-08-03"], [100.0, 110.0])
    assert cross_market._etf_anchor_return(etf_idx, und, sub, None).iloc[1] == \
        pytest.approx(0.10)


def test_build_signals_etf_passes_substitute_fx_from_config():
    """The 7709.HK entry must actually wire substitute_fx through, or the
    back-out silently never runs in production."""
    assert config.CROSS_MARKET_MAP["7709.HK"]["substitute_fx"] == "KRW=X"
    etf, und, sub = _etf_legs()
    fxl = _frame(pd.bdate_range("2025-01-01", periods=300),
                 np.linspace(1400.0, 1450.0, 300))
    seen = []
    loader = lambda t: (seen.append(t) or
                        {"000660.KS": und, "SKHY": sub, "KRW=X": fxl}.get(t))
    cross_market.build_signals(etf, "7709.HK", loader=loader)
    assert "KRW=X" in seen
