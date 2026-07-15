"""Render a mechanical Plan into markdown for OpenClaw / the Feishu bot to read.

The report states only what the evidence produced: direction and conviction from
out-of-sample IC, rule-derived levels, and honest diagnostics (effective breadth,
decorrelation). It deliberately contains no narrative — OpenClaw supplies that."""
from pathlib import Path

import plan as plan_mod

_DIR = {1: "LONG", -1: "SHORT", 0: "FLAT"}


def render_markdown(p: plan_mod.Plan) -> str:
    lines = [
        f"# Indicator Council — {p.asset}",
        "",
        "*Mechanical arm: direction/conviction from out-of-sample IC; every number "
        "is rule-derived. No narrative — analysis is downstream.*",
        "",
        "## Verdict",
        "",
        f"- **Direction:** {_DIR[p.direction]}",
        f"- **Conviction:** {p.conviction:.2f} / 1.00",
        f"- **Regime (context only):** {p.regime_label}",
    ]
    if p.veto:
        lines += ["", f"> **VETO / FLAT** — {p.reason}. No trade."]
    else:
        rr = abs(p.target - p.entry) / abs(p.entry - p.stop) if p.entry != p.stop else float("nan")
        lines += [
            "",
            "## Plan (rule-derived)",
            "",
            "| field | value |",
            "|---|---|",
            f"| entry | {p.entry:.4f} |",
            f"| stop | {p.stop:.4f} |",
            f"| target | {p.target:.4f} |",
            f"| reward:risk | {rr:.2f} |",
            f"| size (frac) | {p.size:.5f} |",
            f"| basis | {p.reason} |",
        ]

    eff_note = " — one set dominates; treat as a single bet, not an ensemble" \
        if 0 < p.effective_n < 1.5 else ""
    lines += [
        "",
        "## Diagnostics (honesty)",
        "",
        f"- **Effective breadth (1/Σw²):** {p.effective_n:.2f}{eff_note}",
        f"- **Max inter-set signal corr:** {p.decorrelation.get('max_abs_corr', 0):.2f}",
    ]
    if p.set_contributions:
        lines += ["", "### Set contributions (weight × signal)", "",
                  "| set | contribution |", "|---|---|"]
        for name, c in sorted(p.set_contributions.items(),
                              key=lambda kv: abs(kv[1]), reverse=True):
            lines.append(f"| {name} | {c:+.4f} |")
    return "\n".join(lines) + "\n"


def write_report(p: plan_mod.Plan, out_dir) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() else "_" for ch in p.asset)
    path = out / f"{safe}.md"
    path.write_text(render_markdown(p), encoding="utf-8")
    return path
