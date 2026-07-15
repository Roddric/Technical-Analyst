# Indicator Council — for OpenClaw

A technical-analysis toolkit. You (OpenClaw) are handed this folder and asked to
"analyze `<TICKER>`". This file is your front door.

## Setup (once)

Self-contained — all reused data/indicator/stats code is vendored under
`vendor/`, so this folder needs no sibling projects. Requires Python 3.11+ and:

```bash
pip install -r requirements.txt
```

The TA library is **`pandas-ta-openbb`** (imported as `pandas_ta`), not vanilla
`pandas_ta`. The **first** analysis of a ticker fetches its history from Yahoo
(needs internet) and caches it under `vendor/price_cache/`; every run after that
is offline and identical (see Reproducibility).

## Analyze a stock — the one command

```bash
python tools.py compute_indicators <TICKER>
```

It fetches history for any Yahoo ticker and prints **one JSON object** with the
classic TA suite plus this system's own quantitative verdict:

```
overview   current price, period high/low, % from each
trend      sma20/50/200 + position, ema stack, golden/death cross + date
momentum   rsi + zone + divergence, macd line/signal/histogram + cross + trend
volatility bollinger bands + percent_b + squeeze, atr + pct + expected range
volume     obv trend/strength + price confirmation + divergence
levels     support / resistance + distance% + risk_reward
council    the mechanical evidence-weighted verdict (read the warning below)
```

Then write the report following `prompt.py` (your analyst persona and the exact
8-section structure). Other commands, if you need them:

```bash
python tools.py get_stock_data <TICKER> [n_rows]   # raw OHLCV rows
python tools.py council <TICKER>                   # council verdict only
```

`null` in the JSON = that indicator was not computable; note it and continue.

## ⚠️ Silence is a valid answer — do not paper over it

The `council` block is deterministic and **never fabricated**. When it returns
`direction: "flat"` / `veto: true` / no `set_contributions`, that means **"no
statistically reliable signal for this stock"** — an honest finding, **not an
error and not a tool failure**.

- **Do not** retry, apologize, or invent a verdict to seem helpful.
- **Do** report the silence plainly and let the classic-indicator analysis stand.
- `effective_breadth < 1.5` means one set dominates — treat the council as a
  single bet, not an ensemble, and say so.

This system is built to *not* manufacture confidence it hasn't earned. Preserve
that at the last mile: report what the numbers say, including when they say
nothing.

## Gate verdict (context for the council numbers)

On the 14-asset test basket: a genuine multi-set ensemble emerges on ~5/14
assets (`effective_breadth` 1.6–3.5); the rest are honestly mute or single-set.
Set decorrelation is measured in-sample and degrades somewhat out-of-sample — so
never oversell "diversification"; lean on the evidence weight, not the count.

## Reproducibility (stable by construction)

Same inputs → same decision, verified byte-identical across repeated runs. Three
things guarantee it:

1. **Data is pinned.** `price_cache/<ticker>.csv` is written on the first fetch
   and read verbatim forever after — it never silently refetches or drifts. To
   intentionally advance the snapshot to newer bars, delete that CSV and re-run.
2. **The engine is deterministic.** Frozen roster + rule-derived levels +
   evidence-weighted arbiter — no randomness in the decision path.
3. **Narration:** run OpenClaw at **temperature 0** and echo the `council`
   verdict verbatim (prompt.py requires this). Identical decisions, near-identical
   prose — the achievable definition of stable.

## Trade log (real track record)

Every time `compute_indicators` produces an **actionable** council plan (long or
short with levels — flat/veto are skipped), it is auto-logged to
`results/trade_log.jsonl`. One open plan per ticker at a time.

To score plans against what actually happened, run **daily after market close**:

```bash
python tools.py update_log
```

Each open plan is held until price **touches its stop or target** (no time cap):
target-first = WIN (+R), stop-first = LOSS (−1R), a bar spanning both counts as
the stop (conservative). Until a level is hit, the plan stays OPEN with a live
unrealized P/L. The command prints a summary JSON whose `markdown` field is a
ready-to-paste table (win rate, avg R, open positions).

**For the bot:** run `python tools.py update_log` once daily after close and
write/refresh the `markdown` table into a Feishu doc — that doc is the durable,
auto-updating track record.

## What's under the hood (you don't need to run these directly)

`indicators.py` classic suite · `selection.py` frozen decorrelated-set selection
· `evidence.py` out-of-sample IC gate + FDR · `arbiter.py` deterministic decision
· `risk.py` rule-derived levels · `run.py` pipeline · `tradelog.py` plan log +
outcome scoring. Tests in `tests/`.
