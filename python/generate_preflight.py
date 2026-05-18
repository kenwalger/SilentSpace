#!/usr/bin/env python3
"""
SilentSpace Guardian — Inbox/Calendar Preflight Audit

Scans all meeting JSON files and flags likely async candidates before the day
begins. Intended for morning scheduling. Writes to reports/preflight_report.md.

Usage:
    python python/generate_preflight.py
"""

import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from audit_meeting import ROOT, REPORTS_DIR, audit_meeting_data, load_meeting

MEETINGS_DIR = ROOT / "meetings"

# A meeting is flagged as an async candidate if it meets two or more of these conditions.
_ASYNC_SIGNALS = [
    ("could_be_email",        lambda m, r: m.get("could_be_email", False)),
    ("no agenda",             lambda m, r: not m.get("has_agenda", True)),
    ("no action items",       lambda m, r: not m.get("has_action_items", True)),
    ("waste score ≥ 60",      lambda m, r: r["waste_score"] >= 60),
]


def _signals_for(meeting: dict, result: dict) -> list[str]:
    return [label for label, check in _ASYNC_SIGNALS if check(meeting, result)]


def _is_async_candidate(meeting: dict, result: dict) -> bool:
    return len(_signals_for(meeting, result)) >= 2


def generate_preflight(results: list[dict]) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    day = datetime.now().strftime("%A")
    time_str = datetime.now().strftime("%H:%M")

    candidates = [r for r in results if _is_async_candidate(r["meeting"], r)]
    safe = [r for r in results if not _is_async_candidate(r["meeting"], r)]

    candidate_rows = "\n".join(
        f"| {r['title']} | {r['waste_score']}/100 | "
        f"{', '.join(_signals_for(r['meeting'], r))} | "
        f"{r['recommendation']} |"
        for r in sorted(candidates, key=lambda r: r["waste_score"], reverse=True)
    ) or "| *(none flagged)* | — | — | — |"

    safe_rows = "\n".join(
        f"| {r['title']} | {r['waste_score']}/100 | {r['classification'].split('—')[0].strip()} |"
        for r in sorted(safe, key=lambda r: r["waste_score"])
    ) or "| *(none)* | — | — |"

    return f"""# Calendar Preflight Audit — {date} ({day})

**Prepared by:** SilentSpace Guardian — Morning Preflight Module
**Filed at:** {time_str}
**Scope:** All meetings in `meetings/` (mocked data)

---

## Preflight Summary

| Metric | Value |
|---|---|
| **Meetings Scanned** | {len(results)} |
| **Async Candidates** | {len(candidates)} |
| **Cleared for Meeting** | {len(safe)} |

> An async candidate meets two or more of: `could_be_email`, no agenda,
> no action items, or waste score ≥ 60.

---

## Flagged — Consider Cancelling or Converting

*These meetings show multiple async signals. Send an email. Post a doc. Reclaim the hour.*

| Meeting | Waste | Async Signals | Recommended Alternative |
|---|---|---|---|
{candidate_rows}

---

## Cleared — Proceeding As Scheduled

*Meetings with fewer than two async signals. They may still be suboptimal.*

| Meeting | Waste | Classification |
|---|---|---|
{safe_rows}

---

*SilentSpace Guardian — Preflight complete. The calendar has been assessed. Attendance is now a choice.*

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

    candidates = [r for r in results if _is_async_candidate(r["meeting"], r)]

    report = generate_preflight(results)
    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = REPORTS_DIR / "preflight_report.md"
    output_path.write_text(report, encoding="utf-8")

    print(f"Preflight report written to: {output_path.relative_to(ROOT).as_posix()}")
    print(f"Meetings scanned: {len(results)}")
    print(f"Async candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
