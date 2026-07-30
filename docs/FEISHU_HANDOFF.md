# Feishu Bot ↔ OpenClaw Handoff Guide

How to wire this Indicator Council system into Feishu so OpenClaw can analyze
stocks on demand, maintain a trade log and watchlist, and receive scheduled
daily technical reports.

The division of labor: **this repo is the deterministic engine** (data +
indicators + mechanical council + trade-log scorer). **OpenClaw is the analyst**
— it runs the engine's commands, reasons over the JSON using the system prompt,
writes the on-demand report, and maintains two Feishu docs. A separate
**GitHub Actions daily pipeline** refreshes configured assets after market close,
reviews the previous seven days, archives the evidence, and can post a report
card into Feishu. The two paths share the same indicator engine and council
verdict.

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

A `cross_market` key also appears, but **only** for configured dual-listed
tickers (`000660.KS`, `7709.HK`). Its absence on every other ticker is normal.

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

### The report MUST follow prompt.py's structure — say this to the bot explicitly

This is the single most common thing to get wrong, because a chat model will
happily produce a fluent, well-written summary in its own shape. That is a
regression, not a style choice: the structure is what makes reports comparable
across tickers and across time. Tell the bot, in these words:

> Every analysis you produce must follow the report structure defined in
> `prompt.py` exactly — all 8 sections, in this order, with their headings:
> 1. STOCK OVERVIEW · 2. TREND ANALYSIS · 3. MOMENTUM · 4. VOLATILITY ·
> 5. VOLUME · 6. KEY LEVELS · 7. INDICATOR CONFLICTS & RISKS · 8. SUMMARY & BIAS
> Do not merge, reorder, rename, or skip sections. If a section's data is
> unavailable, keep the heading and state that it was not computable. Do not
> substitute your own summary format, however good it looks.

The section list is not decoration — each one has required content in
`prompt.py` (e.g. §3 must state whether RSI and MACD agree *or conflict* and
explain the implication either way; §7 must surface conflicts rather than
resolve them; §8 must reconcile explicitly with `council.direction`). If the bot
starts dropping §7 or folding it into §8, that is the failure mode to watch for
— conflicts are the first thing a fluent summary quietly smooths away.

Re-paste the system prompt whenever `prompt.py` changes. If the bot's reports
drift in shape over a long session, re-pasting is the fix.

---

## Step 3 — Give OpenClaw these five commands

OpenClaw calls the engine only through `tools.py`. Grant it permission to run:

| Command | Purpose |
|---|---|
| `python tools.py compute_indicators <TICKER>` | Main call — full indicator suite + council verdict as JSON. Also auto-logs an actionable council plan to the local store. |
| `python tools.py get_stock_data <TICKER> [n_rows]` | Raw OHLCV rows, if the analyst wants to inspect price directly. |
| `python tools.py council <TICKER>` | Just the mechanical council verdict. |
| `python tools.py refresh_data <TICKER>` | Explicitly refresh the pinned cache, retaining the prior valid snapshot if fetching fails. |
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

## Step 6 — Dual-listed tickers (`000660.KS`, `7709.HK`)

Only these two carry a `cross_market` block. When present, fold it into **§6 KEY
LEVELS** as context, and mention it in **§8** only if it changes nothing about
the bias — because it is descriptive, not a signal.

| Ticker | Block says |
|---|---|
| `000660.KS` | SK Hynix local vs US ADR `SKHY`: `premium_pct`, `zone`, `arbitrage_regime`, `regime_note` |
| `7709.HK` | 2× leveraged ETF vs its underlying: `etf_return_pct`, `anchor_return_pct`, `expected_return_pct`, `divergence_pct`, `read` |

**Three rules the bot must not break here:**

1. **`cross_market` is descriptive; `council` is the verdict.** A rich premium or
   an over-reacting ETF is an observation, never a trade signal on its own. The
   mechanical cross-market signals only reach `council` after clearing their
   gates, and **both are still gated today** — so anything you say from this
   block is colour, not evidence.
2. **Before 2026-07-29, do not call SK Hynix's premium "mean-reverting."** Until
   two-way conversion opens there is no arbitrage force to parity — it is a
   one-way scarcity premium. Quote the block's own `regime_note`. Saying "the
   premium is rich, so it should converge" is wrong in this window.
3. **Never infer one listing's direction from another's.** Tested across four
   mature dual-listings, the premium effect did not generalise — two well-powered
   pairs pointed in opposite directions. Do not reason "TSMC's ADR behaves like
   X, so SK Hynix will too." See `docs/cross-market-validation.md`.

If `cross_market.available` is `false`, say the foreign leg was unavailable and
move on. Do not estimate the premium yourself from prices in the report.

---

## Step 7 — Enable scheduled daily reports

The daily asset list is in `daily-report.json`. Circle Internet Group is
configured as `CRCL` by default:

```json
{
  "assets": [
    {"ticker": "CRCL", "name": "Circle Internet Group"}
  ],
  "review_days": 7,
  "validation_horizon": 5
}
```

Test the full daily path from the project folder:

```bash
python daily_report.py --refresh
```

Expect four generated files under `reports/daily/CRCL/`:

- `<MARKET-DATE>.md` and `<MARKET-DATE>.json` — immutable human and machine
  snapshots;
- `latest.md` and `latest.json` — convenient copies of the newest snapshot.

The first report should say that no prior seven-day history exists and that the
validation sample is insufficient. That is correct. Each later run compares the
current facts with reports from the preceding seven calendar days. Once a
directional report has five later trading bars, the forward scorecard evaluates
it. Genuine council flats count as abstentions; bearish evidence suppressed by
the long-only policy is scored as bearish for diagnostics even though no short
trade was taken.

### Turn on the GitHub schedule

The workflow is `.github/workflows/daily-technical-report.yml`. It runs at
22:30 UTC Monday through Friday, which is 06:30 the following day in
Asia/Shanghai and safely after the US close.

In the GitHub repository:

1. Open **Settings → Actions → General → Workflow permissions**.
2. Enable **Read and write permissions** so the job can commit
   `reports/daily/`.
3. If `main` is protected, allow the workflow identity to push or change the
   workflow to open a pull request.
4. Open **Actions → Daily technical reports → Run workflow** once manually.
5. Confirm the dated report was committed before relying on the schedule.

Daily generation does **not** log or open a trade. This is deliberate: report
automation is not trading authorization. Add `--record-trade` only if the owner
explicitly wants the scheduled process to create mechanical plans.

### Turn on Feishu notification

Create a Feishu custom bot for the destination chat, copy its webhook URL, then
add it to GitHub Actions as a repository secret named:

```text
FEISHU_WEBHOOK_URL
```

When that secret exists, the scheduled workflow posts the completed report as
an interactive card. If the secret is absent, generation, validation, archival,
and Git pushing continue normally; only the Feishu notification is skipped.

**Important boundary:** a custom-bot webhook posts a message card into a chat.
It does **not** edit a Feishu cloud document. The existing trade-log and
watchlist documents remain OpenClaw-managed through its Feishu document
permissions. Automatic document replacement would require a Feishu app with
document API credentials and a target document token; those credentials are not
part of this repository and must never be stored in Git.

The detailed operator guide is `docs/daily-report-automation.md`.

---

## Step 8 — Dry-run to confirm the handoff

Ask the bot to analyze one clearly-trending name and one flat/choppy name:

- The trending name should produce a full report; if both arms agree bullish,
  a plan should appear in the trade-log doc with `entry == current price`.
- The flat name should land on the watchlist with its state — no plan.
- Analyze a third ticker and confirm the bot **re-checked** the first two
  watchlist entries in the same turn.
- Manually run the daily workflow and confirm a CRCL report appears in both the
  Git archive and the configured Feishu chat.
- Run it again for the same market date and confirm it replaces that date's
  snapshot rather than creating a duplicate.

Once those checks pass, the bot is live.

---

## Notes & gotchas

- **Determinism:** direction, conviction, and every plan number come from the
  mechanical council — identical inputs give identical plans. OpenClaw never
  invents levels; it narrates and curates.
- **`council.direction == "flat"` is a valid answer**, not an error. It means no
  reliable edge — the bot should report the silence, not retry.
- **Long-only system.** `council.direction` is never `"short"`. If the mechanical
  signal was bearish it is reported as `flat` **with `long_only_suppressed: true`**
  — a bearish read that took no position, NOT a genuine no-edge flat. The bot
  narrates the bearish signal honestly (it informs bias + invalidation) but never
  makes a short plan. On the watchlist, record such a ticker's state as
  `bearish (long-only suppressed)`.
- **Two stores, one truth:** `compute_indicators` auto-appends actionable council
  plans to the local `results/trade_log.jsonl` (the mechanical store). The Feishu
  trade-log doc is the bot's curated view — keep the one-open-plan-per-ticker rule
  so they don't drift.
- **Data availability:** volume-based signals and some levels are `available:
  false` for assets without volume (indices, FX) — that's expected; the bot says
  so rather than inventing values.
- **Latest daily data, not tick data:** `--refresh` advances to the newest daily
  bar available from the provider. The scheduled report must not describe that
  feed as a live intraday quote.
- **Validation language:** the archived five-bar scorecard is prospective
  validation of what reports actually said. It is not a cost-aware portfolio
  backtest and makes no performance claim before 20 directional reports mature.
