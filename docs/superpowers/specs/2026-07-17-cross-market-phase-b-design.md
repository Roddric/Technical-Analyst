# Cross-Market Linkage — Phase B: 07709 Leveraged-ETF Divergence

**Date:** 2026-07-17
**Status:** Approved design, pending implementation plan
**Builds on:** Phase A (`cross_market.py`, `2026-07-17-cross-market-linkage-design.md`)

## One-line

Add a mechanical divergence signal for `7709.HK` — the HK-listed **2× leveraged
ETF** on SK Hynix — that detects when the ETF over/under-reacts relative to 2× its
underlying's move, as a mean-reversion signal on the ETF's own forward return. It
runs `7709.HK` as its own council target, reusing the Phase A cross-market
machinery. The edge, like Phase A's, must earn its weight out-of-sample.

## Motivation

`7709.HK` is a 2× daily-leveraged ETF tracking `000660.KS`. When it moves more
than 2× the underlying (leverage decay, HK/Korea liquidity gaps, market-maker
hedging limits — e.g. a Korea-holiday over-reaction), that excess tends to
revert as MM create/redeem arbitrage re-couples price to the underlying. That
reversion is a tradable signal on the ETF itself — distinct from Phase A's ADR
premium (a different tradable, on a different instrument).

## The empirical methodology finding (the correctness anchor)

The spec's earlier assumption ("FX-adjust the anchor to HKD") is **wrong by
evidence.** Regressing 7709.HK daily returns on the underlying (n=159):

| Anchor return | β (slope) | corr | R² |
|---|---|---|---|
| **000660.KS KRW return (no FX)** | **1.775** | **0.966** | **0.933** |
| 000660.KS HKD-translated (with FX) | 1.676 | 0.959 | 0.920 |

The ETF tracks the **KRW (local) return** better; adding the FX term degrades the
fit. So the anchor return is the plain **KRW return, no FX adjustment.** The β of
1.78 (not exactly 2) is normal leverage-ETF friction/decay + slight HK-vs-Korea
close-timing — and it is harmless here because the divergence is **z-scored**: the
rolling mean absorbs that systematic 2-vs-1.78 gap, leaving only genuine
over/under-reaction. Correlation 0.966 confirms a real 2× tracker, so the
divergence residual (~3–7%) is exactly the signal.

## Scope & non-goals

- Extend `cross_market.py` with an ETF-divergence signal + snapshot, and add a
  `7709.HK` entry to `CROSS_MARKET_MAP`. No changes to arbiter/risk/plan.
- **Non-goals:** intraday-NAV premium (not on daily bars); currency-hedged
  variant (evidence says the plain KRW anchor fits); Phase A is untouched.

## Data (probe-confirmed)

- ETF symbol is **`7709.HK`** (not `07709.HK`, which 404s) — 166 bars, ~HK$44.80.
- `000660.KS` underlying (6634 bars), `SKHY` substitute anchor (5 bars), `HKD=X`
  available but **not needed** (no FX in the anchor per the finding above).
- yfinance fetch path already in place (Phase A `price_cache._fetch_yf`).

## Integration — `7709.HK` as its own council target

`CROSS_MARKET_MAP` gains an ETF-shaped entry; `build_signals` dispatches by the
keys present (ADR-shaped `{"adr": ...}` → ADR signals; ETF-shaped
`{"underlying": ...}` → divergence). `analyze_ticker("7709.HK")` runs the normal
council on the ETF and appends `xmkt_etf_divergence`, gated on 7709.HK's own
forward return through the existing `evidence` machinery.

```python
CROSS_MARKET_MAP = {
    "000660.KS": {"adr": "SKHY", "fx": "KRW=X", "adr_ratio": 10.0},   # Phase A
    "7709.HK":   {"underlying": "000660.KS", "substitute": "SKHY",     # Phase B
                  "leverage": 2.0},
}
```

## The signal — `xmkt_etf_divergence`

```
etf_return[D]    = 7709.HK close pct_change
anchor_return[D] = 000660.KS KRW return on the SAME date D (Korea's 15:30 KST close
                   precedes HK's 16:00 HKT close, so it is causally available);
                   where Korea did NOT trade date D (holiday), fall back to the
                   SKHY overnight return (strictly-before) — the substitute anchor.
divergence[D]    = etf_return[D]  −  leverage × anchor_return[D]        (leverage = 2.0)
xmkt_etf_divergence = causal z-score(divergence, XMKT_Z_WINDOW)
```

Sign (expected negative — fade the over-reaction) and weight are learned OOS, not
hardcoded. `leverage` is the **nominal 2.0**; the z-score removes the empirical
1.78-vs-2 friction bias, so no rolling-beta fit is needed.

### Anchor construction (causal, holiday-aware)

- `und_ret` = `000660.KS` KRW `pct_change`, indexed by Korea dates.
- `und_on_etf` = `und_ret.reindex(etf.index)` — same-date Korea return where both
  markets traded; **NaN** on Korea holidays (HK open, Korea closed).
- `skhy_overnight` = SKHY return as-of **strictly-before** each ETF date (causal).
- `anchor_return = und_on_etf.fillna(skhy_overnight)` — same-date Korea, else the
  SKHY overnight substitute. (Datetime resolutions coerced to `ns` before reindex,
  per the Phase A `_asof_align` fix.)

This is the mechanical form of the "Korea-holiday over-reaction" case: when Korea
is shut, the ETF is priced against the stale/SKHY reference and tends to
over-shoot, which the divergence captures.

## Descriptive snapshot — `etf_divergence_snapshot`

A live descriptive block for `7709.HK` (latest ETF return, latest anchor return,
latest `divergence`, and whether the ETF is over- or under-reacting vs 2×), so
OpenClaw can narrate the "today's ETF drop is liquidity/decay, not fundamentals"
read. Uses latest available prints; graceful `{"available": false}` when data is
missing.

## Honest limits (documented)

- **Vol-decay confound.** Without intraday NAV, the daily divergence can't fully
  separate real mispricing from mechanical 2× decay; the z-score de-means the
  *systematic* part, but residual noise remains. The OOS gate decides if a
  tradable reversion survives it.
- **Not emittable yet.** 166 ETF bars − 60-bar z-warmup ≈ 105 finite < 150
  `XMKT_MIN_HISTORY`, so the mechanical signal stays absent (`build_signals → {}`)
  for ~2 more months. The descriptive snapshot works now.
- **No July-29 dependency.** Unlike the ADR premium, 07709 reversion is
  MM-create/redeem-driven, not ADR-conversion-driven — no regime split needed.
- **Substitute-anchor currency.** SKHY overnight is USD-return, used as a KRW-move
  proxy on Korea holidays only (rare, second-order daily FX difference); accepted.

## Testing (load-bearing)

- **Divergence math:** on fixtures, `divergence = etf_ret − 2×anchor_ret` exactly;
  z-scored output named `xmkt_etf_divergence`.
- **Substitute anchor fires only on Korea holidays:** an ETF date with a matching
  Korea bar uses the Korea return; an ETF date with NO Korea bar uses the SKHY
  overnight — assert the coalesce picks the right source per date.
- **Causal alignment:** same-date Korea is allowed (Korea precedes HK close), but
  a *future* Korea/SKHY print never enters an ETF row; mixed datetime resolutions
  handled (reuse the Phase A regression case).
- **Dispatch:** `build_signals("7709.HK")` yields `{"xmkt_etf_divergence": ...}`
  when history suffices, `{}` otherwise; `build_signals("000660.KS")` still yields
  the ADR signals (Phase A unchanged).
- **Graceful degradation / no non-finite:** missing underlying/ETF/substitute →
  signal absent or snapshot `available:false`; nothing non-finite propagates.
- **Integration:** `analyze_ticker("7709.HK")` runs clean and appends the
  divergence to the pool (OOS-gated) once history suffices.

## Defaults summary

| Param | Default | Where |
|---|---|---|
| ETF symbol | `7709.HK` | `config.CROSS_MARKET_MAP` |
| underlying / substitute | `000660.KS` / `SKHY` | `config.CROSS_MARKET_MAP` |
| leverage | 2.0 (nominal; z-score handles 1.78 friction) | `config.CROSS_MARKET_MAP` |
| anchor FX | none (KRW return — evidence-backed) | `cross_market.py` |
| z-score window / min history | 60 / 150 (shared with Phase A) | `config` |

## Open items (resolve in plan)

1. `build_signals` dispatch: branch on `"adr" in cfg` vs `"underlying" in cfg`;
   keep both paths independently testable.
2. Whether the descriptive `etf_divergence_snapshot` is wired into
   `tools.compute_indicators` for `7709.HK` now, or deferred with the mechanical
   signal (leaning: wire the snapshot now — it's useful pre-history).
