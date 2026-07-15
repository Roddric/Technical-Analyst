# Indicator Council — for OpenClaw

A technical-analysis toolkit. You (OpenClaw) are handed this folder and asked to
"analyze `<TICKER>`". This file is your front door.

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

## What's under the hood (you don't need to run these directly)

`indicators.py` classic suite · `selection.py` frozen decorrelated-set selection
· `evidence.py` out-of-sample IC gate + FDR · `arbiter.py` deterministic decision
· `risk.py` rule-derived levels · `run.py` pipeline. Tests in `tests/`.
