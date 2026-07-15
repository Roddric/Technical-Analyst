"""Decorrelated-set selection (Option 1), train-walled.

Replaces round-robin bundle construction. Every choice below is made on the
TRAIN slice only; the holdout is never consulted during selection, so the search
over indicator combinations cannot leak look-ahead into the later OOS scoring.
Train forward returns are computed from `close[:split]` alone, so even the last
HORIZON train bars never peek across the split. K emerges from the data (<=MAX_SETS)."""
import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

import config
config.ensure_reuse_on_path()
import stats as st
import sets as sets_mod

SLOTS = sets_mod.SLOTS
NULL_NAME = sets_mod.NULL_NAME
ROSTER_DIR = Path(__file__).resolve().parent / "results" / "rosters"


def _roster_config() -> dict:
    """The config knobs that define a selection; a change invalidates a frozen roster."""
    return {"SLOT_KEEP": config.SLOT_KEEP, "MAX_SETS": config.MAX_SETS,
            "DECORR_THRESHOLD": config.DECORR_THRESHOLD, "ERR_WINDOW": config.ERR_WINDOW,
            "HORIZON": config.HORIZON, "TRAIN_FRAC": config.TRAIN_FRAC}


def _roster_path(key: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in key)
    return ROSTER_DIR / f"{safe}.json"


def load_frozen_roster(key: str) -> list[list[str]] | None:
    """Return a previously frozen roster iff it exists and was built under the
    current selection config; else None."""
    path = _roster_path(key)
    if not path.exists():
        return None
    rec = json.loads(path.read_text())
    if rec.get("config") != _roster_config():
        return None                      # config changed -> stale, must re-freeze
    return [list(b) for b in rec["roster"]]


def freeze_roster(df: pd.DataFrame, key: str, mode: str = "log") -> list[list[str]]:
    """Select the roster on the train slice and persist it (member names + train
    boundary + config). Frozen: never recomputed once written for this key/config."""
    roster = select_roster(df, mode)
    split = sets_mod._train_slice(len(df))
    ROSTER_DIR.mkdir(parents=True, exist_ok=True)
    _roster_path(key).write_text(json.dumps({
        "key": key, "roster": roster, "config": _roster_config(),
        "n_train": int(split), "n_total_at_freeze": int(len(df)),
        "train_end": str(df.index[split - 1].date()),
    }, indent=2))
    return roster


def _train_fwd(df: pd.DataFrame, split: int, mode: str) -> np.ndarray:
    """Forward returns computed from train prices only (length == split)."""
    return st.forward_returns(df["close"].to_numpy("float64")[:split], config.HORIZON, mode)


def _sign(z_train: np.ndarray, fwd_train: np.ndarray) -> float:
    ic, _, _, _ = st.spearman_ic_hac(z_train, fwd_train, lag=config.HORIZON)
    return -1.0 if (np.isfinite(ic) and ic < 0) else 1.0


def _train_ic(signed_train: np.ndarray, fwd_train: np.ndarray) -> float:
    ic, _, _, _ = st.spearman_ic_hac(signed_train, fwd_train, lag=config.HORIZON)
    return ic if np.isfinite(ic) else 0.0


def _err_series(signed_train: np.ndarray, fwd_train: np.ndarray) -> pd.Series:
    """Rolling train-IC series (the 'error' series used for decorrelation)."""
    return pd.Series(st.rolling_spearman(signed_train, fwd_train, config.ERR_WINDOW))


def _err_corr(a: pd.Series, b: pd.Series) -> float:
    c = a.corr(b)
    return 0.0 if not np.isfinite(c) else abs(float(c))


def _signed_slot_members(df, split, fwd_train):
    """slot -> list of (name, train_sign, train_ic, err_series) with train IC > 0, best first."""
    by_slot = sets_mod._candidates_by_slot(df)
    out = {}
    for slot, zs in by_slot.items():
        members = []
        for z in zs:
            zt = z.to_numpy("float64")[:split]
            sign = _sign(zt, fwd_train)
            signed_t = sign * zt
            ic = _train_ic(signed_t, fwd_train)
            if ic <= 0:
                continue
            members.append((z.name, sign, ic, _err_series(signed_t, fwd_train)))
        members.sort(key=lambda m: m[2], reverse=True)
        out[slot] = members
    return out


def _reduce_slot(members, keep, threshold):
    reps = []
    for m in members:
        if all(_err_corr(m[3], r[3]) < threshold for r in reps):
            reps.append(m)
        if len(reps) >= keep:
            break
    return reps


def select_roster(df: pd.DataFrame, mode: str = "log") -> list[list[str]]:
    """Selected roster as a list of bundles (each a list of member names).
    Deterministic; train-slice only."""
    n = len(df)
    split = sets_mod._train_slice(n)
    fwd_train = _train_fwd(df, split, mode)
    by_slot = sets_mod._candidates_by_slot(df)
    ztrain = {z.name: z.to_numpy("float64")[:split] for zs in by_slot.values() for z in zs}

    slot_reps = {s: _reduce_slot(m, config.SLOT_KEEP, config.DECORR_THRESHOLD)
                 for s, m in _signed_slot_members(df, split, fwd_train).items()}
    active = [s for s in SLOTS if slot_reps.get(s)]
    if not active:
        return []

    bundles = []
    for combo in product(*(slot_reps[s] for s in active)):
        names = [c[0] for c in combo]
        signs = {c[0]: c[1] for c in combo}
        signed_t = np.mean([signs[nm] * ztrain[nm] for nm in names], axis=0)
        ic = _train_ic(signed_t, fwd_train)
        if ic <= 0:
            continue
        bundles.append((names, ic, _err_series(signed_t, fwd_train)))
    bundles.sort(key=lambda b: b[1], reverse=True)

    roster, roster_err = [], []
    for names, ic, err in bundles:
        if all(_err_corr(err, e) < config.DECORR_THRESHOLD for e in roster_err):
            roster.append(names)
            roster_err.append(err)
        if len(roster) >= config.MAX_SETS:
            break
    return roster


def build_selected_sets(df: pd.DataFrame, mode: str = "log",
                        roster_key: str | None = None) -> dict[str, pd.Series]:
    """Full-length composite per selected bundle (Set1..SetK) plus the Null
    tripwire. Composites span full history; signs and selection use train only.

    If `roster_key` is given, the roster is FROZEN: loaded from disk if present
    (built under the current config), otherwise selected once and persisted, and
    never recomputed again. With no key the roster is selected live (tests)."""
    n = len(df)
    split = sets_mod._train_slice(n)
    fwd_train = _train_fwd(df, split, mode)
    by_slot = sets_mod._candidates_by_slot(df)
    lookup = {z.name: z for zs in by_slot.values() for z in zs}

    if roster_key is not None:
        roster = load_frozen_roster(roster_key) or freeze_roster(df, roster_key, mode)
    else:
        roster = select_roster(df, mode)

    signals: dict[str, pd.Series] = {}
    for i, names in enumerate(roster, start=1):
        members = []
        for nm in names:
            z = lookup.get(nm)
            if z is None:                    # frozen member not computable on this df
                continue
            sign = _sign(z.to_numpy("float64")[:split], fwd_train)
            members.append(sign * z)
        if not members:
            continue
        comp = pd.concat(members, axis=1).mean(axis=1)
        signals[f"Set{i}"] = comp.rename(f"Set{i}")

    rng = np.random.default_rng(config.NULL_SEED)
    null_z = sets_mod.causal_zscore(pd.Series(rng.standard_normal(n), index=df.index))
    null_sign = _sign(null_z.to_numpy("float64")[:split], fwd_train)
    signals[NULL_NAME] = (null_sign * null_z).rename(NULL_NAME)
    return signals
