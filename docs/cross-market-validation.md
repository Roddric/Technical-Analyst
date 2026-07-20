# Cross-Market Validation — does the ADR premium effect generalise?

**Date:** 2026-07-20
**Status:** Complete. **Result: the hypothesis FAILED.**

## Why this was run

Two questions were tangled together: (1) does "ADR premium reversion" work as an
idea at all, and (2) does it work for SK Hynix specifically. Question (2) is
unanswerable today — 000660.KS/SKHY has almost no post-conversion history. But
question (1) can be answered now using mature dual-listings that have had
ordinary two-way arbitrage for years.

## Method (pre-registered before any result was seen)

- Signals exactly as implemented, no code changes; `regime_start=None` (all
  mature), z-window 60, horizon 5.
- Metric: out-of-sample Spearman IC on the holdout with a Newey-West HAC t-stat
  (`evidence.set_ic_stats`), gated by `evidence.compute_weights`
  (GATE_K 1.65, FDR_Q 0.10).
- **Primary hypothesis:** `xmkt_adr_premium` IC is *positive*, matching TSM.
- **Secondary:** `xmkt_adr_overnight` shows no significant edge.
- Power stated in advance: a sign test on 4 pairs gives p=0.0625 even if all
  four agree — suggestive, never decisive.

Pairs were chosen to be maximally *unlike* each other (sector, region, arbitrage
regime) so a shared result could not be an artifact of clustering on Asian
semiconductor ADRs. ADR ratios were fixed from prospectus facts and confirmed
against the implied par ratio *before* testing — a units check, not a signal fit.

## Results

| pair | sector / region | premium IC | t | n | ratio (implied par) |
|---|---|---|---|---|---|
| 2330.TW / TSM | semis / Taiwan | **+0.0873** | **+2.31** | 1975 | 0.2 (0.2 exact) |
| 7203.T / TM | autos / Japan | +0.0183 | +0.48 | 735 | 0.1 (0.1005) |
| NOVO-B.CO / NVO | pharma / Denmark | −0.0343 | −1.22 | 1924 | 1.0 (1.0037) |
| SHEL.L / SHEL | energy / UK | **−0.0743** | **−2.03** | 1060 | 50.0 (49.889) |

**2/4 positive — exactly chance.** The sign test yields nothing.

## Conclusions

1. **The premium mechanic does not generalise.** TSM's result is pair-specific.
   TSM has a structural, well-documented persistent premium (foreign-ownership
   limits, US demand) that Toyota, Novo and Shell do not.
2. **Two well-powered pairs disagree in direction** with comparable magnitude
   (TSM +2.31, Shell −2.03). Taking |t| two-sided, both would survive
   Benjamini-Hochberg at q=0.10 — with opposite signs. That points at genuine
   pair-specific structure, not pure noise.
3. **The sign must be fit per pair and cannot be borrowed.** In particular it
   cannot be carried from TSM to SK Hynix.
4. **The overnight leg is a clean null** — negative or flat in all four pairs,
   no pair above |t|=1.3. The most solid finding here.
5. The gate behaved correctly: weight 0.000 everywhere except TSM. The system
   did not manufacture an edge from three nulls.

## Caveats

- Toyota (n=735) and Shell (n=1060) have thinner holdouts than Novo (n=1924).
  Toyota is capped by the `period="10y"` fetch fallback, Shell by its ADR ticker
  change from RDS.A in 2022. Neither null is as well-powered as the table
  suggests — though the two pairs leaning negative include the best-powered one.
- TSM was nominated as a favourable candidate before testing, so its result
  carries a selection effect that the other three do not.

## Reproducing

Re-add the four entries to `CROSS_MARKET_MAP` (`regime_start=None` for all) and
run `evidence.set_ic_stats` / `compute_weights` per pair. They are kept out of
production config on purpose: they are not trading targets, and all four
correctly earn zero weight.
