# Daily technical report archive

This directory is written by `daily_report.py` and committed by the scheduled
GitHub Actions workflow.

Each configured asset gets:

- `YYYY-MM-DD.md` — the human-readable report for that market date;
- `YYYY-MM-DD.json` — the exact indicator packet, comparison, and validation data;
- `latest.md` / `latest.json` — convenient pointers to the newest archive.

The dated JSON files are the forward-validation ledger. Do not rewrite old
snapshots: their value comes from preserving what the system actually knew and
said on that date.
