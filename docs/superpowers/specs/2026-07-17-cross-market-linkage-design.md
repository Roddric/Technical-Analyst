# Cross-Market Linkage: SK Hynix across Korea / US ADR / HK 2× ETF

**Date:** 2026-07-17
**Status:** Approved design, pending implementation plan

## One-line

Add cross-listing signals for SK Hynix — treating `000660.KS` (Korea, the price-
discovery anchor), `US.SKHY` (the US ADR, same underlying), and `07709` (a HK 2×
leveraged ETF) as one asset priced in three venues — and let the mechanical
council decide, on out-of-sample evidence, whether the overnight ADR lead and the
cross-listing premium actually predict returns. No number is trusted on the story
alone; the OOS gate decides.

## Motivation

`000660.KS` is the world's dominant HBM supplier and trades in three venues with
non-overlapping-to-partially-overlapping hours. Two real, tradable structures
exist: (1) **transmission** — when Korea is closed, the US ADR moves on US/AI
sentiment and leads the next Korean session; (2) **premium** — the same equity's
price can diverge across venues (ADR premium/discount; ETF over/under-reaction),
and tends to converge. Both are only real if built **causally** (using only data
available before the bar being predicted). Non-synchronous trading is where naive
cross-market work manufactures un-tradable alpha; this spec makes causal alignment
the load-bearing invariant.

## Scope & phases

Built in **two phases**, each gated on its own OOS evidence before scaling.

- **Phase A — `000660.KS` cross-listing signals (core).** Two mechanical signals
  fed into the existing `000660.KS` council: ADR overnight transmission + ADR
  premium reversion. Plus a live descriptive premium snapshot for narration.
- **Phase B — `07709` leveraged-ETF divergence (add-on, separate target).** A
  daily leverage-tracking-divergence reversion signal for trading `07709` itself.

**Non-goals:** intraday NAV (not available on daily bars — see Phase B caveat);
general N-venue framework (config-driven for `000660.KS` first, per the project's
"gate before you scale" habit); any change to the arbiter/risk/plan layers.

## Venue model & causal foundation (the correctness spine)

Assumed **daily close ordering** within a calendar date D (all convertible to a
common clock; KST = UTC+9, HKT = UTC+8, EST = UTC−5):

| Venue | Local close | In KST | Order on date D |
|---|---|---|---|
| Korea `000660.KS` | 15:30 KST | 15:30 KST **D** | first |
| HK `07709` | 16:00 HKT | 17:00 KST **D** | second |
| US `US.SKHY` | 16:00 EST | 06:00 KST **D+1** | third (prints next KST day) |

Consequences that define every merge in this design:

- **At Korea's date-D close**, the freshest US print available is `US.SKHY` **date
  D−1** (which closed 06:00 KST D). `US.SKHY` date D has *not* printed yet.
- **At HK's date-D close**, `000660.KS` date D (closed 2.5h earlier) *is*
  available; `US.SKHY` date D is not.

**Alignment rule = as-of backward merge, per target, encoded from the table
above** (`pandas.merge_asof(direction="backward")`, holiday-robust, never a naive
`shift`):

- **Phase A** (target = `000660.KS` date D): attach `US.SKHY` and `KRW=X` with
  **local date strictly < D** (`allow_exact_matches=False`). A US print dated D
  must never enter the D bar.
- **Phase B** (target = `07709` date D): attach the underlying anchor with the
  Korea leg allowed **same-date** (`000660.KS` date D precedes the HK close), and
  when Korea did **not** trade that date (holiday), fall back to `US.SKHY` date
  D−1 as the **substitute anchor** — this is exactly the holiday over-reaction
  case.

This is the load-bearing invariant and gets the dedicated test (below), the
cross-market twin of the swing-pivot causal-confirmation test.

## Phase A — `000660.KS` cross-listing signals

**Module** `cross_market.py` — sole owner of cross-listing signal construction.
Loads the foreign legs, aligns them causally, returns named signal series aligned
to the target index. Plugs into `run.analyze_asset` **after**
`selection.build_selected_sets(...)`: for any asset in the config map, its
cross-market signals are appended to the signal dict, then flow through
`evidence.compute_weights` → `arbiter` unchanged — same t-gate + FDR as every
other signal.

**Config**
```
CROSS_MARKET_MAP = {
  "000660.KS": {"adr": "US.SKHY", "fx": "KRW=X", "adr_ratio": 1.0,
                "etf": "07709", "etf_fx": "HKD=X", "etf_leverage": 2.0},
}
XMKT_Z_WINDOW = 60        # rolling window for causal z-scores
XMKT_MIN_HISTORY = 150    # bars of aligned overlap required before emitting
```

**Signal 1 — `xmkt_adr_overnight` (transmission).** The `US.SKHY` return over the
US session that closed strictly before the Korea bar (as-of aligned), causal
z-scored over `XMKT_Z_WINDOW`. Same underlying → the most direct overnight lead.
Sign (expected +) and weight are learned OOS by `evidence.py`, not hardcoded.

**Signal 2 — `xmkt_adr_premium` (premium reversion).** FX-adjust the ADR to KRW:
`adr_krw = US.SKHY($) × (KRW=X) × adr_ratio`; the ADR premium is
`adr_krw / 000660.KS − 1`, built on the causally-aligned legs. Provide the causal
z-score of the premium series over `XMKT_Z_WINDOW`. Mean-reversion (expected
negative sign — fade the stretched premium) is learned by `evidence.py`; the ±3%
human band is the sanity check, not the mechanical threshold.

**Live descriptive snapshot.** Separately expose the *current* ADR premium
(latest available print of each venue, e.g. the −1.35% example) and its band
classification (>+3% rich / <−3% cheap / within band) for OpenClaw to narrate —
this uses latest prints, not the causal history, because it describes "now."

## Phase B — `07709` leveraged-ETF divergence (separate target)

`07709` is a 2× fund on the same underlying, denominated in HKD. Its NAV-premium
(price vs intraday NAV) cannot be computed on daily bars, so we use the
daily-feasible proxy:

```
anchor_ret[D] = return of the underlying anchor over 07709's date-D period,
                FX-adjusted to HKD  (000660.KS date D if Korea traded, else the
                US.SKHY overnight — the substitute anchor)
divergence[D] = actual 07709 return[D]  −  etf_leverage × anchor_ret[D]
xmkt_etf_divergence = causal z-score(divergence, XMKT_Z_WINDOW)
```

A move beyond `leverage ×` the anchor is over/under-reaction → mean-reversion.
This is a **separate tradable**: it is gated on `07709`'s *own* forward return, not
mixed into the `000660.KS` decision.

**Documented caveat (must appear in output/notes):** without intraday NAV, this
daily divergence conflates genuine premium/discount with the mechanical vol-decay
of a 2× fund; it is a **noisy proxy**. The OOS gate decides whether a tradable
reversion survives the decay noise. If an intraday-NAV feed is added later, this
signal is upgraded to a true price-vs-NAV premium.

## Data & prerequisites (verify before build)

1. **Fetchable history** for `US.SKHY`, `KRW=X`, `07709`, `HKD=X` via the loader.
   The user reports the data is obtained; confirm each loads to the standard
   lowercase OHLCV schema on a `DatetimeIndex`.
2. **ADR conversion ratio** (`adr_ratio`, tentatively 1:1) — pin and verify. A
   wrong ratio biases every premium reading by a constant multiplicative factor.
3. **ADR liquidity check** (a measurement, not an assumption): if `US.SKHY` is a
   thin OTC mirror re-priced off the Korea close, its premium is mostly FX +
   staleness with little independent US information — expect the OOS gate to give
   the transmission/premium signals ~0 weight. That is the gate working, not a
   bug; but measure US-hours volume/price-discovery so the result is interpretable.

## Honest limits (documented, not hidden)

- **Strong-but-not-hard arbitrage.** ADR convergence is not instantaneous (Korea
  foreign-ownership limits, ADR conversion frictions), so the premium is a lean
  toward reversion, not a forced close.
- **Daily FX timing.** `KRW=X` daily close (≈ NY close) does not coincide with
  Korea's 15:30 KST close; the premium inherits a small FX-timing error. Acceptable
  on daily bars; noted.
- **07709 vol-decay confound** (Phase B, above).
- **Momentum double-count.** `xmkt_adr_overnight` may correlate with the existing
  momentum sets; include it in the decorrelation report so breadth isn't oversold.

## Testing (load-bearing)

- **Causal alignment (the spine):** on synthetic multi-venue calendars, assert a
  foreign print dated D never enters the Phase-A target-D row (only ≤ D−1), no
  future leak; and that the Phase-B substitute-anchor fires exactly on Korea-
  holiday dates. This is the cross-market twin of the swing-pivot causal test.
- **No-lookahead end-to-end:** a signal computed on data up to D is unchanged when
  later bars are appended (mirrors the existing `run` no-lookahead test).
- **FX + ADR-ratio applied:** premium math reproduces a hand-computed value (e.g.
  the −1.35% worked example) from fixed inputs.
- **Signal math on fixtures:** transmission z-score sign, premium residual, and the
  `divergence = actual − leverage×anchor` identity on known inputs.
- **Integration + gating:** `000660.KS` surfaces the two Phase-A signals; on data
  with no cross-listing edge they earn ~0 weight (honest gate). `07709` divergence
  gates on `07709`'s own forward return.
- **Graceful degradation:** insufficient aligned overlap (< `XMKT_MIN_HISTORY`) or
  a missing foreign leg → the signal is absent/NaN, never a crash or a fabricated
  value; nothing non-finite reaches downstream.

## Defaults summary

| Param | Default | Where |
|---|---|---|
| z-score window | 60 | `cross_market.py` |
| min aligned history | 150 | `cross_market.py` |
| ADR conversion ratio | 1.0 (verify) | `config.CROSS_MARKET_MAP` |
| ETF leverage | 2.0 | `config.CROSS_MARKET_MAP` |
| alignment | as-of backward, per-venue close order | `cross_market.py` |

## Open questions (resolve in plan)

1. Does the loader fetch `US.SKHY` / `07709` / `KRW=X` / `HKD=X`, or is a
   fetch path a prerequisite task?
2. Confirmed `adr_ratio` value.
3. Phase-B target wiring: does `07709` reuse the full council pipeline as a second
   target, or a standalone reversion-signal path? (Leaning standalone — it needs
   only the one divergence signal, not the full roster machinery.)
