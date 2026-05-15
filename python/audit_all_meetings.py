#!/usr/bin/env python3
"""
SilentSpace Guardian — Batch Meeting Auditor

Audits every JSON file in meetings/, generates individual Markdown reports,
and writes a summary report to reports/summary_report.md.

Usage:
    python python/audit_all_meetings.py
"""

import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from audit_meeting import (
    ROOT,
    REPORTS_DIR,
    ensure_cobol_binary,
    generate_report,
    load_meeting,
    save_report,
    score_meeting,
)
from classify import async_recommendation, classify_meeting

MEETINGS_DIR = ROOT / "meetings"

# Weekly recurrence multiplier: how many times per week does this meeting occur?
RECURRENCE_MULTIPLIER = {
    "none":     0.0,   # one-off — no ongoing weekly cost
    "monthly":  0.25,
    "biweekly": 0.5,
    "weekly":   1.0,
    "daily":    5.0,
}

# Failure modes: (display label, predicate)
FAILURE_MODES = [
    ("Could be an email",              lambda m: m.get("could_be_email", False)),
    ("No agenda distributed",          lambda m: not m.get("has_agenda", True)),
    ("No action items expected",       lambda m: not m.get("has_action_items", True)),
    ("Excessive attendees (> 6)",      lambda m: len(m.get("attendees", [])) > 6),
    ("Duration exceeds one hour",      lambda m: m.get("duration_minutes", 0) > 60),
    ("Frequent recurrence",            lambda m: m.get("recurrence", "none") in ("weekly", "daily")),
]


def _verdict_short(classification: str) -> str:
    """First clause of a classification label, before the em-dash."""
    return classification.split("—")[0].strip()


def _focus_hours_recovered(results: list[dict]) -> float:
    """Weekly focus hours from cancelling meetings with waste_score >= 60."""
    total = 0.0
    for r in results:
        if r["waste_score"] >= 60:
            m = r["meeting"]
            hrs = m.get("duration_minutes", 0) / 60
            total += hrs * RECURRENCE_MULTIPLIER.get(m.get("recurrence", "none"), 0.0)
    return round(total, 1)


def _most_common_failure(results: list[dict]) -> str:
    counts: Counter = Counter()
    for r in results:
        for label, check in FAILURE_MODES:
            if check(r["meeting"]):
                counts[label] += 1
    if not counts:
        return "None identified."
    label, n = counts.most_common(1)[0]
    pct = round(n / len(results) * 100)
    return f'"{label}" — present in {n} of {len(results)} meetings ({pct}%)'


def audit_all(bin_path: Path, wsl_prefix: list[str]) -> list[dict]:
    meeting_files = sorted(MEETINGS_DIR.glob("*.json"))
    if not meeting_files:
        print(f"No meeting files found in {MEETINGS_DIR}", file=sys.stderr)
        sys.exit(1)

    results = []
    for path in meeting_files:
        meeting = load_meeting(str(path))
        waste_score, necessity_prob = score_meeting(meeting, bin_path, wsl_prefix)
        classification = classify_meeting(waste_score)
        recommendation = async_recommendation(meeting, waste_score)

        report = generate_report(
            meeting, waste_score, necessity_prob, classification, recommendation
        )
        save_report(meeting.get("title", path.stem), report)

        results.append({
            "title": meeting.get("title", path.stem),
            "meeting": meeting,
            "waste_score": waste_score,
            "necessity_prob": necessity_prob,
            "classification": classification,
        })

        print(f"  {waste_score:3d}/100  {meeting.get('title', path.stem)}")

    return results


def generate_summary(results: list[dict]) -> str:
    n = len(results)
    avg_waste = round(sum(r["waste_score"] for r in results) / n)
    avg_necessity = round(sum(r["necessity_prob"] for r in results) / n)
    recovered = _focus_hours_recovered(results)
    failure = _most_common_failure(results)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    by_waste = sorted(results, key=lambda r: r["waste_score"], reverse=True)

    verdict_counts = Counter(_verdict_short(r["classification"]) for r in results)
    verdict_rows = "\n".join(
        f"| {v} | {c} |"
        for v, c in sorted(verdict_counts.items(), key=lambda x: -x[1])
    )

    top3 = "\n".join(
        f"{i + 1}. **{r['title']}** — {r['waste_score']}/100 waste, "
        f"{r['necessity_prob']}% necessity"
        for i, r in enumerate(by_waste[:3])
    )

    all_rows = "\n".join(
        f"| {r['title']} | {r['waste_score']}/100 | {r['necessity_prob']}% "
        f"| {_verdict_short(r['classification'])} |"
        for r in by_waste
    )

    return f"""# SilentSpace Guardian — Batch Audit Summary

*{n} meetings audited on {timestamp}*

---

## By the Numbers

| Metric | Value |
|---|---|
| **Meetings Audited** | {n} |
| **Average Waste Score** | {avg_waste}/100 |
| **Average Necessity Probability** | {avg_necessity}% |
| **Estimated Weekly Focus Hours Recovered** | {recovered} hrs |

> Focus hours recovered: cumulative weekly time from meetings scoring ≥ 60,
> weighted by recurrence. One-off meetings are excluded (sunk cost, not ongoing).

---

## Verdict Breakdown

| Classification | Count |
|---|---|
{verdict_rows}

---

## Top 3 Worst Offenders

{top3}

---

## Most Common Failure Mode

{failure}

---

## All Meetings (sorted by waste score)

| Meeting | Waste | Necessity | Verdict |
|---|---|---|---|
{all_rows}

---

*SilentSpace Guardian v0.1.0 — Protecting calendars, one audit at a time.*
"""


def main() -> None:
    width = 62
    print()
    print("=" * width)
    print("  SilentSpace Guardian -- Batch Audit")
    print("=" * width)
    print()

    bin_path, wsl_prefix = ensure_cobol_binary()
    results = audit_all(bin_path, wsl_prefix)

    n = len(results)
    avg_waste = round(sum(r["waste_score"] for r in results) / n)
    recovered = _focus_hours_recovered(results)

    summary = generate_summary(results)
    REPORTS_DIR.mkdir(exist_ok=True)
    summary_path = REPORTS_DIR / "summary_report.md"
    summary_path.write_text(summary, encoding="utf-8")

    print()
    print(f"  Meetings audited       : {n}")
    print(f"  Average waste score    : {avg_waste}/100")
    print(f"  Weekly focus hrs saved : {recovered} hrs")
    print()
    print(f"  Individual reports     : reports/")
    print(f"  Summary report         : reports/summary_report.md")
    print()
    print("=" * width)
    print()


if __name__ == "__main__":
    main()
