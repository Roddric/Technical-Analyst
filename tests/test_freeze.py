import json

import numpy as np
import selection


def test_freeze_then_load_is_stable(synth_ohlcv, tmp_path, monkeypatch):
    monkeypatch.setattr(selection, "ROSTER_DIR", tmp_path)
    df = synth_ohlcv(seed=8, drift=0.002)
    roster1 = selection.freeze_roster(df, "TESTKEY")
    assert selection._roster_path("TESTKEY").exists()
    roster2 = selection.load_frozen_roster("TESTKEY")
    assert roster1 == roster2                       # persisted verbatim


def test_frozen_roster_not_recomputed_when_more_data_arrives(synth_ohlcv, tmp_path, monkeypatch):
    # The whole point of freezing: growing the data must NOT change the roster.
    monkeypatch.setattr(selection, "ROSTER_DIR", tmp_path)
    df = synth_ohlcv(seed=8, drift=0.002, n=800)
    frozen = selection.freeze_roster(df, "GROWKEY")
    more = synth_ohlcv(seed=8, drift=0.002, n=900)   # 100 extra bars
    sig = selection.build_selected_sets(more, roster_key="GROWKEY")
    used = [k for k in sig if k.startswith("Set")]
    assert len(used) == len(frozen)                  # same roster reused, not re-selected


def test_config_change_invalidates_frozen_roster(synth_ohlcv, tmp_path, monkeypatch):
    monkeypatch.setattr(selection, "ROSTER_DIR", tmp_path)
    df = synth_ohlcv(seed=8, drift=0.002)
    selection.freeze_roster(df, "CFGKEY")
    monkeypatch.setattr(selection.config, "MAX_SETS", 3)   # changed selection config
    assert selection.load_frozen_roster("CFGKEY") is None  # stale -> ignored
