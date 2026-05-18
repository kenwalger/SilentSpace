#!/usr/bin/env python3
"""
SilentSpace Guardian — Daily Meeting Regret Audit

Audits all meeting JSON files in meetings/ and writes a daily digest to
reports/daily_digest.md. Intended for weekday evening scheduling (5 PM).

Usage:
    python python/generate_daily_digest.py
"""

import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from audit_meeting import ROOT, REPORTS_DIR, audit_meeting_data, load_meeting

MEETINGS_DIR = ROOT / "meetings"


def _async_candidates(results: list[dict]) -> list[dict]:
    return [r for r in results if r["meeting"].get("could_be_email", False)]


def _top_offenders(results: list[dict], n: int = 3) -> list[dict]:
    return sorted(results, key=lambda r: r["waste_score"], reverse=True)[:n]


def generate_daily_digest(results: list[dict]) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    day = datetime.now().strftime("%A")
    n = len(results)
    avg_waste = round(sum(r["waste_score"] for r in results) / n) if n else 0
    candidates = _async_candidates(results)
    offenders = _top_offenders(results)

    offender_rows = "\n".join(
        f"| {r['title']} | {r['waste_score']}/100 | {r['necessity_prob']}% | {r['recommendation']} |"
        for r in offenders
    )

    candidate_rows = "\n".join(
        f"| {r['title']} | {r['waste_score']}/100 | {r['recommendation']} |"
        for r in candidates
    ) or "| *(none flagged)* | — | — |"

    return f"""# Daily Meeting Regret Audit — {date} ({day})

**Prepared by:** SilentSpace Guardian — Daily Regret Module
**Scope:** All meetings in `meetings/` (mocked data)

---

## Day-End Summary

| Metric | Value |
|---|---|
| **Meetings Reviewed** | {n} |
| **Average Waste Score** | {avg_waste}/100 |
| **Async Candidates** | {len(candidates)} |
| **High-Waste Meetings (≥ 81)** | {sum(1 for r in results if r["waste_score"] >= 81)} |

---

## Priority Regret Targets

*Meetings that most deserved to be emails, Slack messages, or silence.*

| Meeting | Waste | Necessity | Recommended Alternative |
|---|---|---|---|
{offender_rows}

---

## Async Candidates

*Meetings where `could_be_email` is true. These should not have happened.*

| Meeting | Waste Score | Recommended Alternative |
|---|---|---|
{candidate_rows}

---

*SilentSpace Guardian — Filed at {datetime.now().strftime("%H:%M")}. No meeting was held to review this report.*

The meeting has been remembered.
This is not a compliment.
"""


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

    digest = generate_daily_digest(results)
    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = REPORTS_DIR / "daily_digest.md"
    output_path.write_text(digest, encoding="utf-8")

    print(f"Daily digest written to: {output_path.relative_to(ROOT).as_posix()}")
    print(f"Meetings reviewed: {len(results)}")
    print(f"Async candidates: {len(_async_candidates(results))}")


if __name__ == "__main__":
    main()
