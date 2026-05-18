#!/usr/bin/env python3
"""
SilentSpace Guardian — Weekly Entropy Summary

Audits all meeting JSON files, focuses on recurring meetings, and writes a
weekly entropy summary to reports/weekly_entropy.md. Intended for Friday
afternoon scheduling.

Usage:
    python python/generate_weekly_entropy.py
"""

import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from audit_meeting import ROOT, REPORTS_DIR, audit_meeting_data, load_meeting

MEETINGS_DIR = ROOT / "meetings"

# Approximate weekly occurrences for each recurrence level
WEEKLY_OCCURRENCES = {
    "none":     0.0,
    "monthly":  0.25,
    "biweekly": 0.5,
    "weekly":   1.0,
    "daily":    5.0,
}

RECURRENCE_LABELS = {
    "none":     "One-time",
    "monthly":  "Monthly",
    "biweekly": "Biweekly",
    "weekly":   "Weekly",
    "daily":    "Daily",
}


def _weekly_waste_hours(result: dict) -> float:
    m = result["meeting"]
    occ = WEEKLY_OCCURRENCES.get(m.get("recurrence", "none"), 0.0)
    hrs = m.get("duration_minutes", 0) / 60
    return round(hrs * occ * len(m.get("attendees", [])), 2)


def generate_weekly_entropy(results: list[dict]) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    recurring = [r for r in results if r["meeting"].get("recurrence", "none") != "none"]
    one_time = [r for r in results if r["meeting"].get("recurrence", "none") == "none"]

    total_weekly_hours = sum(_weekly_waste_hours(r) for r in recurring if r["waste_score"] >= 61)

    recurring_rows = "\n".join(
        f"| {r['title']} | "
        f"{RECURRENCE_LABELS.get(r['meeting'].get('recurrence','none'),'?')} | "
        f"{r['waste_score']}/100 | "
        f"{r['necessity_prob']}% | "
        f"{_weekly_waste_hours(r):.1f} |"
        for r in sorted(recurring, key=lambda r: r["waste_score"], reverse=True)
    ) or "| *(none)* | — | — | — | — |"

    high_waste_recurring = [r for r in recurring if r["waste_score"] >= 61]

    return f"""# Weekly Entropy Summary — {date}

**Prepared by:** SilentSpace Guardian — Weekly Entropy Module
**Distribution:** Internal Use Only

---

## Overview

| Metric | Value |
|---|---|
| **Total Meetings** | {len(results)} |
| **Recurring Meetings** | {len(recurring)} |
| **One-Time Meetings** | {len(one_time)} |
| **Recurring Waste Score ≥ 61** | {len(high_waste_recurring)} |
| **Est. Weekly Person-Hours Lost (high-waste recurring)** | {total_weekly_hours:.1f} hrs |

> Person-hours lost: (duration_minutes / 60) × attendees × weekly_occurrences,
> for recurring meetings scoring ≥ 61 on the Waste Index.

---

## Recurring Meeting Breakdown

*Sorted by waste score. These repeat. That is the problem.*

| Meeting | Cadence | Waste | Necessity | Est. Weekly Hrs Lost |
|---|---|---|---|---|
{recurring_rows}

---

## Pattern Analysis

**Total recurring waste patterns identified:** {len(high_waste_recurring)}

{_pattern_analysis(recurring)}

---

## Remediation Priority

{_remediation_priority(high_waste_recurring)}

---

*SilentSpace Guardian — Weekly filing. The calendar does not audit itself.*

The meeting has been remembered.
This is not a compliment.
"""


def _pattern_analysis(recurring: list[dict]) -> str:
    if not recurring:
        return "No recurring meetings in dataset."

    no_agenda = [r for r in recurring if not r["meeting"].get("has_agenda", True)]
    no_actions = [r for r in recurring if not r["meeting"].get("has_action_items", True)]
    could_be_email = [r for r in recurring if r["meeting"].get("could_be_email", False)]

    lines = []
    if no_agenda:
        lines.append(
            f"- **{len(no_agenda)} recurring meeting(s) have no agenda.** "
            "Recurrence without structure is scheduled confusion."
        )
    if no_actions:
        lines.append(
            f"- **{len(no_actions)} recurring meeting(s) generate no action items.** "
            "They produce attendance, not output."
        )
    if could_be_email:
        lines.append(
            f"- **{len(could_be_email)} recurring meeting(s) could be emails.** "
            "They are not emails. This is a choice."
        )
    return "\n".join(lines) if lines else "No significant patterns identified this week."


def _remediation_priority(high_waste: list[dict]) -> str:
    if not high_waste:
        return "No high-waste recurring meetings requiring immediate action."

    top = sorted(high_waste, key=lambda r: r["waste_score"], reverse=True)[:3]
    rows = "\n".join(
        f"{i+1}. **{r['title']}** — waste {r['waste_score']}/100, "
        f"{RECURRENCE_LABELS.get(r['meeting'].get('recurrence','?'),'?')} cadence. "
        f"{r['recommendation']}"
        for i, r in enumerate(top)
    )
    return rows


def main() -> None:
    meeting_files = sorted(MEETINGS_DIR.glob("*.json"))
    if not meeting_files:
        print(f"No meeting files found in {MEETINGS_DIR}", file=sys.stderr)
        sys.exit(1)

    results = []
    for path in meeting_files:
        meeting = load_meeting(str(path))
        try:
            result = audit_meeting_data(meeting)
        except ValueError as exc:
            print(f"WARNING: Skipping {path.name}: {exc}", file=sys.stderr)
            continue
        results.append(result)

    if not results:
        print("ERROR: No valid meetings to process.", file=sys.stderr)
        sys.exit(1)

    report = generate_weekly_entropy(results)
    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = REPORTS_DIR / "weekly_entropy.md"
    output_path.write_text(report, encoding="utf-8")

    recurring_count = sum(1 for r in results if r["meeting"].get("recurrence", "none") != "none")
    print(f"Weekly entropy report written to: {output_path.relative_to(ROOT).as_posix()}")
    print(f"Meetings reviewed: {len(results)}")
    print(f"Recurring meetings: {recurring_count}")


if __name__ == "__main__":
    main()
