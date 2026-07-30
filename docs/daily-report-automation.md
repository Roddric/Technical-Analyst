# Daily report automation

The daily pipeline turns the deterministic Indicator Council engine into a
durable reporting loop:

1. explicitly refresh the requested ticker and any configured cross-market legs;
2. compute the classic indicators and council verdict;
3. compare the new snapshot with reports from the prior seven calendar days;
4. score any archived directional calls that have matured after five trading bars;
5. save Markdown and JSON, optionally notify Feishu, then commit the archive.

Circle Internet Group is configured as `CRCL` in `daily-report.json`.

## Run locally

Install the normal runtime dependencies, then:

```bash
python daily_report.py --refresh
```

This reads the asset list from `daily-report.json`. To run an ad-hoc ticker:

```bash
python daily_report.py NVDA --refresh
```

Reports are written under `reports/daily/<TICKER>/`. A rerun for the same market
date atomically replaces that date's files instead of creating duplicates.
Report generation does not open or log a trade by default. Add `--record-trade`
only when the scheduled reporting process is also authorized to create plans.

The normal engine remains pinned and reproducible. Refreshing is opt-in:

```bash
python tools.py refresh_data CRCL
python tools.py compute_indicators CRCL
```

If a refresh fails, the previous valid cache is retained. The report discloses
whether the refresh succeeded, failed partially, or was skipped.

## Scheduled GitHub run

`.github/workflows/daily-technical-report.yml` runs at 22:30 UTC Monday through
Friday—06:30 the next day in Asia/Shanghai and safely after the US close. It
commits `reports/daily/` back to the current branch.

Repository setup:

1. Enable GitHub Actions.
2. In **Settings → Actions → General → Workflow permissions**, allow
   **Read and write permissions**.
3. If `main` is protected, allow this workflow/bot to push or change the final
   step to open a pull request.
4. Use **Actions → Daily technical reports → Run workflow** for the first manual
   run. Confirm the dated CRCL report before relying on the schedule.

The schedule generates reports only on weekdays. Exchange holidays are safe:
the run overwrites the latest market-date snapshot and does not invent a new bar.

## Feishu notification

Add a repository Actions secret named `FEISHU_WEBHOOK_URL` containing a Feishu
custom-bot webhook. When the secret exists, the workflow sends the completed
report as an interactive card. Without it, archival and Git pushing continue;
publishing is simply skipped.

For a local publishing test:

```bash
FEISHU_WEBHOOK_URL='https://…' python daily_report.py CRCL --refresh --publish-feishu
```

The webhook is read only from the environment and is never written into a report
or committed.

## What the validation section means

The report contains two different evidence layers:

- The council itself gates signals using out-of-sample IC and FDR.
- The archive scorecard tests what the daily reports subsequently did over the
  configured five-trading-bar horizon.

Genuine flat council calls are counted as abstentions. A bearish signal suppressed
by the long-only policy is scored as bearish for diagnostic purposes, even though
the system did not take a short trade. The report refuses to claim validation
until at least 20 directional reports have matured.

This prospective scorecard is more honest than repeatedly fitting a backtest to
the same history, but it is not a complete strategy backtest. It does not yet
model transaction costs, slippage, portfolio constraints, or benchmark-relative
performance; the report states that limitation on every run.

## Configuration

`daily-report.json` supports multiple assets:

```json
{
  "assets": [
    {"ticker": "CRCL", "name": "Circle Internet Group"},
    {"ticker": "NVDA", "name": "NVIDIA"}
  ],
  "review_days": 7,
  "validation_horizon": 5
}
```

Keep the dated JSON archives. They are the immutable evidence needed to review
past reports and validate forecasts without hindsight.
