# Feishu Bot ↔ OpenClaw Handoff Guide

How to wire this Indicator Council system into the Feishu bot so OpenClaw can
analyze stocks on demand, maintain a trade log, and run a watchlist.

The division of labor: **this repo is the deterministic engine** (data +
indicators + mechanical council + trade-log scorer). **OpenClaw is the analyst**
— it runs the engine's commands, reasons over the JSON using the system prompt,
writes the report, and maintains two Feishu docs. No scheduler: everything runs
on-demand when the owner asks the bot to analyze something.

---

## Step 1 — Put the engine somewhere the bot can run it

OpenClaw needs shell access to this folder on a machine with **Python 3.11+**.

```bash
cd indicator-council
pip install -r requirements.txt          # NOTE: TA lib is pandas-ta-openbb, imported as pandas_ta
```

Smoke-test the engine before touching Feishu:

```bash
python tools.py compute_indicators AAPL
```

Expect one JSON object with keys `overview, trend, momentum, volatility, volume,
levels, support_resistance, fibonacci, council` and no traceback. If that works,
the engine is ready.

---

## Step 2 — Load the system prompt into OpenClaw

The bot's **system prompt** is the string in `prompt.py`. Extract it verbatim:

```bash
python -c "import prompt; print(prompt.SYSTEM_PROMPT)"
```

Paste that as OpenClaw's system prompt (or point the bot's config at it). This is
what defines the 8-section report, the 5-step workflow, and the OPERATIONAL
ACTIONS (plan / trade-log / watchlist). When you change behavior, you change
`prompt.py` — nowhere else.

---

## Step 3 — Give OpenClaw these four commands

OpenClaw calls the engine only through `tools.py`. Grant it permission to run:

| Command | Purpose |
|---|---|
| `python tools.py compute_indicators <TICKER>` | Main call — full indicator suite + council verdict as JSON. Also auto-logs an actionable council plan to the local store. |
| `python tools.py get_stock_data <TICKER> [n_rows]` | Raw OHLCV rows, if the analyst wants to inspect price directly. |
| `python tools.py council <TICKER>` | Just the mechanical council verdict. |
| `python tools.py update_log` | Re-scores every open plan against fresh prices; returns a Feishu-ready markdown table under `"markdown"`. |

`<TICKER>` is any Yahoo symbol (e.g. `AAPL`, `NVDA`, `BTC-USD`, `^FTSE`, `0700.HK`).

---

## Step 4 — Create the two Feishu docs the bot maintains

1. **Trade-log doc.** The curated record of bullish+confident plans the bot has
   committed to. Mirror the table `update_log` produces — columns:
   `ticker | dir | entry_date | entry | stop | target | status | result`.
   One open plan per ticker at a time.

2. **Watchlist doc.** Every analyzed ticker that did **not** qualify as
   bullish+confident. Columns: `ticker | last state | date`
   (state e.g. `council flat`, `bearish`, `disagreement: council long / bias neutral`).

Give OpenClaw read/write access to both. The bot reads the watchlist doc to know
what to re-check, and writes both docs as part of OPERATIONAL ACTIONS.

---

## Step 5 — The per-request runbook (what happens each time)

When the owner asks the bot to analyze `<TICKER>`:

1. **Analyze** — run `python tools.py compute_indicators <TICKER>`, reason through
   the 5 layers, write the 8-section report (now including swing-pivot S/R zones
   and Fibonacci levels in KEY LEVELS).
2. **Decide qualification** — a ticker is **BULLISH + CONFIDENT only if both arms
   agree**: `council.direction == "long"` and not vetoed, **AND** OpenClaw's own
   Section-8 bias is `BULLISH` with `high` confidence. Anything else (bearish,
   flat, neutral, moderate/low confidence, or a one-arm disagreement) does **not**
   qualify.
3. **If it qualifies** → build the trading plan from the council's rule-derived
   `entry / stop / target / size_fraction` verbatim. **Entry = the latest current
   price** (`overview.current_price`, which equals `council.entry`). Append the
   plan to the **trade-log doc** (skip if that ticker already has an open plan),
   then run `python tools.py update_log` and sync its `markdown` into the doc.
4. **If it does not qualify** → add/update it on the **watchlist doc** with its
   current state and today's date.
5. **Re-check the watchlist** — for every ticker already on the watchlist, run
   `compute_indicators` and re-evaluate step 2. If any has **flipped to
   bullish+confident**: alert the owner at the top of the response, run step 3 for
   it (make + upload the plan), and remove it from the watchlist. Tickers still
   not qualifying stay on the list silently.

---

## Step 6 — Dry-run to confirm the handoff

Ask the bot to analyze one clearly-trending name and one flat/choppy name:

- The trending name should produce a full report; if both arms agree bullish,
  a plan should appear in the trade-log doc with `entry == current price`.
- The flat name should land on the watchlist with its state — no plan.
- Analyze a third ticker and confirm the bot **re-checked** the first two
  watchlist entries in the same turn.

Once those three behaviors show up, the bot is live.

---

## Notes & gotchas

- **Determinism:** direction, conviction, and every plan number come from the
  mechanical council — identical inputs give identical plans. OpenClaw never
  invents levels; it narrates and curates.
- **`council.direction == "flat"` is a valid answer**, not an error. It means no
  reliable edge — the bot should report the silence, not retry.
- **Two stores, one truth:** `compute_indicators` auto-appends actionable council
  plans to the local `results/trade_log.jsonl` (the mechanical store). The Feishu
  trade-log doc is the bot's curated view — keep the one-open-plan-per-ticker rule
  so they don't drift.
- **Data availability:** volume-based signals and some levels are `available:
  false` for assets without volume (indices, FX) — that's expected; the bot says
  so rather than inventing values.
