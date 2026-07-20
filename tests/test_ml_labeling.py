"""Step 1 tests — forward-return labelling.

A label legitimately looks forward; the discipline is knowing WHEN it may be
used. These tests pin the knowability boundary and the overlap purge, which are
where the leak actually lives.
"""
import numpy as np
import pandas as pd
import pytest

import config
config.ensure_reuse_on_path()

from ml_patterns.labeling.geometric_forward_return import (
    forward_return_labels, trainable_mask, purge_overlapping,
)


def _ohlcv(closes):
    closes = np.asarray(closes, dtype=float)
    idx = pd.bdate_range("2024-01-01", periods=len(closes))
    return pd.DataFrame({"open": closes, "high": closes, "low": closes,
                         "close": closes, "volume": np.ones(len(closes))}, index=idx)


def test_forward_return_matches_hand_calc():
    df = _ohlcv([100.0, 110.0, 121.0, 133.1, 146.41])
    lab = forward_return_labels(df, horizon=1, mode="log")
    assert lab["fwd_return"].iloc[0] == pytest.approx(np.log(110 / 100))
    assert lab["fwd_return"].iloc[3] == pytest.approx(np.log(146.41 / 133.1))


def test_last_h_labels_are_nan_structural_guard():
    """vendor/stats.assert_no_lookahead is re-asserted inside the labeler; this
    pins the property it guards."""
    df = _ohlcv(np.linspace(100, 200, 30))
    for h in (1, 5, 10):
        lab = forward_return_labels(df, horizon=h)
        assert lab["fwd_return"].iloc[-h:].isna().all()
        assert lab["fwd_return"].iloc[:-h].notna().all()


def test_label_is_not_knowable_before_t_plus_h():
    df = _ohlcv(np.linspace(100, 200, 20))
    h = 5
    lab = forward_return_labels(df, horizon=h)
    # the label for bar 3 becomes known at bar 8, not before
    assert lab["known_at_pos"].iloc[3] == 8
    assert lab["known_at"].iloc[3] == df.index[8]
    # tail labels never become knowable inside this frame
    assert lab["known_at_pos"].iloc[-h:].isna().all()
    assert lab["known_at"].iloc[-h:].isna().all()


def test_trainable_mask_excludes_labels_not_yet_known():
    df = _ohlcv(np.linspace(100, 200, 40))
    h = 5
    lab = forward_return_labels(df, horizon=h)
    mask = trainable_mask(lab, asof_pos=20, horizon=h)
    # as of bar 20, labels up to bar 15 are known; 16+ are not
    assert mask[15] and not mask[16]
    assert not mask[20]
    # every admitted row must have a known_at_pos at or before the as-of bar
    admitted = lab.loc[mask, "known_at_pos"].to_numpy()
    assert (admitted <= 20).all()


def test_trainable_mask_embargo_pushes_the_boundary_back():
    df = _ohlcv(np.linspace(100, 200, 40))
    h, emb = 5, 3
    lab = forward_return_labels(df, horizon=h)
    plain = trainable_mask(lab, asof_pos=20, horizon=h, embargo=0)
    embargoed = trainable_mask(lab, asof_pos=20, horizon=h, embargo=emb)
    assert embargoed.sum() == plain.sum() - emb
    assert embargoed[12] and not embargoed[13]


def test_purge_drops_rows_whose_forward_window_touches_the_test_block():
    df = _ohlcv(np.linspace(100, 300, 60))
    h = 5
    lab = forward_return_labels(df, horizon=h)
    mask = purge_overlapping(lab, test_start_pos=30, test_end_pos=39, horizon=h)
    # the test block itself is never trainable
    assert not mask[30:40].any()
    # rows in [25, 30) have forward windows reaching into the block -> purged
    assert not mask[25:30].any()
    assert mask[24]
    # rows after the block are trainable again (no embargo requested)
    assert mask[40]


def test_purge_embargo_extends_past_the_test_block():
    df = _ohlcv(np.linspace(100, 300, 60))
    h = 5
    lab = forward_return_labels(df, horizon=h)
    mask = purge_overlapping(lab, test_start_pos=30, test_end_pos=39,
                             horizon=h, embargo=4)
    assert not mask[40:44].any()
    assert mask[44]


def test_labels_are_truncation_invariant_where_defined():
    """Appending future bars must not change an already-defined label. Only the
    previously-NaN tail may fill in."""
    rng = np.random.default_rng(5)
    closes = 100 * np.cumprod(1 + rng.normal(0, 0.02, 120))
    df = _ohlcv(closes)
    h = 5
    full = forward_return_labels(df, horizon=h)
    cut = 80
    partial = forward_return_labels(df.iloc[:cut], horizon=h)
    defined = partial["fwd_return"].notna()
    np.testing.assert_allclose(
        partial.loc[defined, "fwd_return"].to_numpy(),
        full.iloc[:cut].loc[defined, "fwd_return"].to_numpy())


def test_direction_is_the_sign_of_the_forward_return():
    df = _ohlcv([100.0, 105.0, 95.0, 95.0, 110.0, 100.0])
    lab = forward_return_labels(df, horizon=1)
    assert lab["direction"].iloc[0] == 1.0      # 100 -> 105
    assert lab["direction"].iloc[1] == -1.0     # 105 -> 95
    assert lab["direction"].iloc[2] == 0.0      # 95 -> 95 (flat)
    assert np.isnan(lab["direction"].iloc[-1])  # no future


def test_empty_frame_does_not_crash():
    lab = forward_return_labels(_ohlcv([]), horizon=5)
    assert len(lab) == 0
    assert trainable_mask(lab, asof_pos=0).sum() == 0
    assert purge_overlapping(lab, 0, 1).sum() == 0
