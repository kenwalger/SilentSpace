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

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


def _most_common_failure(results: list[dict]) -> tuple[str, int, int]:
    """Return (label, count, pct) for the most prevalent failure mode."""
    counts: Counter = Counter()
    for r in results:
        for label, check in FAILURE_MODES:
            if check(r["meeting"]):
                counts[label] += 1
    if not counts:
        return "None identified.", 0, 0
    label, n = counts.most_common(1)[0]
    pct = round(n / len(results) * 100)
    return label, n, pct


def _count_spiritually_async(results: list[dict]) -> int:
    """Meetings that could have been emails."""
    return sum(1 for r in results if r["meeting"].get("could_be_email", False))


def _count_heat_death(results: list[dict]) -> int:
    """Meetings classified as Corporate Heat Death Events (waste >= 81)."""
    return sum(1 for r in results if r["waste_score"] >= 81)


def _count_visibility_rituals(results: list[dict]) -> int:
    """Meetings with no agenda, no action items, and more than 3 attendees.
    These exist to be witnessed, not to accomplish anything."""
    return sum(
        1 for r in results
        if not r["meeting"].get("has_agenda", True)
        and not r["meeting"].get("has_action_items", True)
        and len(r["meeting"].get("attendees", [])) > 3
    )


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
            "recommendation": recommendation,
        })

        print(f"  {waste_score:3d}/100  {meeting.get('title', path.stem)}")

    return results


def generate_summary(results: list[dict]) -> str:
    n = len(results)
    avg_waste = round(sum(r["waste_score"] for r in results) / n)
    avg_necessity = round(sum(r["necessity_prob"] for r in results) / n)
    recovered = _focus_hours_recovered(results)
    failure_label, failure_count, failure_pct = _most_common_failure(results)
    spiritually_async = _count_spiritually_async(results)
    heat_death = _count_heat_death(results)
    visibility_rituals = _count_visibility_rituals(results)
    timestamp = datetime.now().strftime("%Y-%m-%d")

    by_waste = sorted(results, key=lambda r: r["waste_score"], reverse=True)

    tier_counts = Counter(_verdict_short(r["classification"]) for r in results)
    tier_rows = "\n".join(
        f"| {tier} | {count} | {round(count / n * 100)}% |"
        for tier, count in sorted(tier_counts.items(), key=lambda x: -x[1])
    )

    remediation_rows = "\n".join(
        f"| {i + 1} | {r['title']} | {r['waste_score']}/100 | "
        f"{r['necessity_prob']}% | {r['recommendation']} |"
        for i, r in enumerate(by_waste[:3])
    )

    asset_rows = "\n".join(
        f"| {r['title']} | {r['waste_score']}/100 | {r['necessity_prob']}% "
        f"| {_verdict_short(r['classification'])} |"
        for r in by_waste
    )

    return f"""# Organizational Entropy Report

**Period Assessed:** {timestamp}
**Prepared by:** SilentSpace Guardian — Calendar Governance Module v0.1.0
**Distribution:** Internal Use Only

---

## Calendar Damage Assessment

| Indicator | Value |
|---|---|
| **Meetings Audited** | {n} |
| **Average Waste Score** | {avg_waste} / 100 |
| **Average Necessity Probability** | {avg_necessity}% |
| **Focus Hours Recovered (est. weekly)** | {recovered} hrs |
| **Meetings Spiritually Async** | {spiritually_async} |
| **Corporate Heat Death Events** | {heat_death} |
| **Executive Visibility Rituals** | {visibility_rituals} |

> Focus hours recovered: estimated weekly time returned to focused work by cancelling
> or converting meetings scoring ≥ 60 on the Waste Index. One-time events are excluded
> from the weekly projection as the loss has already occurred.
>
> Meetings Spiritually Async: meetings that are, at their core, an email.
> Executive Visibility Rituals: recurring meetings with no agenda, no action items,
> and more than three attendees. They exist to be witnessed.

---

## Entropy Distribution by Classification

| Classification | Count | Share |
|---|---|---|
{tier_rows}

---

## Priority Remediation Targets

The three meetings with the highest waste scores are listed below.
Remediation is recommended at the earliest opportunity that does not itself require a meeting.

| # | Meeting | Waste | Necessity | Recommended Remediation |
|---|---|---|---|---|
{remediation_rows}

---

## Root Cause Summary

**Primary Entropy Driver:** "{failure_label}"
Identified in {failure_count} of {n} meetings ({failure_pct}%).

Meetings without expected outputs generate discussion without obligation. This pattern
suggests a structural misalignment between calendar activity and organizational output.
It is not, at this time, considered an anomaly.

---

## Full Asset Register

*All meetings assessed in this reporting period, sorted by waste score.*

| Meeting | Waste | Necessity | Classification |
|---|---|---|---|
{asset_rows}

---

*SilentSpace Guardian v0.1.0 — Issued automatically. No meeting was held to review this report.*
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
