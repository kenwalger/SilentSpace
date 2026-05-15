#!/usr/bin/env python3
"""
SilentSpace Guardian — Meeting Audit Engine

Reads a meeting JSON, runs it through the COBOL entropy scorer,
classifies the result, and writes a Markdown report to reports/.

Usage:
    python python/audit_meeting.py meetings/weekly_alignment_sync.json
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from classify import async_recommendation, classify_meeting

ROOT = Path(__file__).parent.parent
COBOL_SRC = ROOT / "cobol" / "entropy_engine.cob"
COBOL_BIN = ROOT / "cobol" / "entropy_engine"
COBOL_BIN_WIN = ROOT / "cobol" / "entropy_engine.exe"
REPORTS_DIR = ROOT / "reports"

RECURRENCE_LEVELS = {
    "none": 0,
    "monthly": 1,
    "biweekly": 2,
    "weekly": 3,
    "daily": 4,
}


def _to_wsl_path(p: Path) -> str:
    """Convert a Windows absolute path to its WSL /mnt/ equivalent."""
    s = str(p)
    if len(s) >= 2 and s[1] == ":":
        return f"/mnt/{s[0].lower()}" + s[2:].replace("\\", "/")
    return s.replace("\\", "/")


def _compile_native() -> None:
    print("Compiling COBOL entropy engine...")
    result = subprocess.run(
        ["cobc", "-x", "-o", str(COBOL_BIN), str(COBOL_SRC)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("COBOL compilation failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("Compilation successful.\n")


def _wsl_distro() -> str:
    """Return the name of the first WSL distro that has cobc."""
    for distro in ("Ubuntu", "Debian"):
        r = subprocess.run(
            ["wsl", "-d", distro, "--", "which", "cobc"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            return distro
    # Fall back to whatever the default distro is
    return ""


def _compile_wsl() -> None:
    print("Compiling COBOL entropy engine via WSL...")
    distro = _wsl_distro()
    wsl_cmd = ["wsl", "-d", distro, "--"] if distro else ["wsl", "--"]
    result = subprocess.run(
        wsl_cmd + ["cobc", "-x", "-o", _to_wsl_path(COBOL_BIN), _to_wsl_path(COBOL_SRC)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("COBOL compilation failed (WSL):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("Compilation successful.\n")


def ensure_cobol_binary() -> tuple[Path, bool]:
    """Return (bin_path, use_wsl). Compiles the binary if absent."""
    if COBOL_BIN_WIN.exists():
        return COBOL_BIN_WIN, False
    if COBOL_BIN.exists():
        return COBOL_BIN, False

    if shutil.which("cobc"):
        _compile_native()
        return (COBOL_BIN_WIN if COBOL_BIN_WIN.exists() else COBOL_BIN), False

    if shutil.which("wsl"):
        _compile_wsl()
        return COBOL_BIN, True

    print(
        "ERROR: GnuCOBOL (cobc) not found.\n"
        "  macOS : brew install gnu-cobol\n"
        "  Linux : sudo apt install gnucobol\n"
        "  Windows: install WSL then: sudo apt install gnucobol",
        file=sys.stderr,
    )
    sys.exit(1)


def load_meeting(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score_meeting(meeting: dict, bin_path: Path, use_wsl: bool = False) -> tuple[int, int]:
    duration = str(meeting.get("duration_minutes", 60))
    attendees = str(len(meeting.get("attendees", [])))
    has_agenda = "1" if meeting.get("has_agenda", False) else "0"
    has_actions = "1" if meeting.get("has_action_items", False) else "0"
    could_be_email = "1" if meeting.get("could_be_email", False) else "0"
    recurrence = str(RECURRENCE_LEVELS.get(meeting.get("recurrence", "none"), 0))

    stdin_data = "\n".join([duration, attendees, has_agenda,
                             has_actions, could_be_email, recurrence]) + "\n"
    if use_wsl:
        distro = _wsl_distro()
        wsl_cmd = ["wsl", "-d", distro, "--"] if distro else ["wsl", "--"]
        cmd = wsl_cmd + [_to_wsl_path(bin_path)]
    else:
        cmd = [str(bin_path)]

    result = subprocess.run(cmd, input=stdin_data, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Entropy engine error:\n{result.stderr}")

    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        raise ValueError(f"Unexpected entropy engine output: {result.stdout!r}")

    return int(lines[0].strip()), int(lines[1].strip())


def generate_report(meeting: dict, waste_score: int, necessity_prob: int) -> str:
    title = meeting.get("title", "Untitled Meeting")
    classification = classify_meeting(waste_score)
    recommendation = async_recommendation(meeting, waste_score)
    attendees = meeting.get("attendees", [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    waste_bar = "#" * (waste_score // 10) + "-" * (10 - waste_score // 10)
    necessity_bar = "#" * (necessity_prob // 10) + "-" * (10 - necessity_prob // 10)

    return f"""# Meeting Audit Report: {title}

*Generated by SilentSpace Guardian on {timestamp}*

---

## Meeting Details

| Field | Value |
|---|---|
| **Title** | {title} |
| **Organizer** | {meeting.get("organizer", "Unknown")} |
| **Duration** | {meeting.get("duration_minutes", "?")} minutes |
| **Attendees** | {len(attendees)} — {", ".join(attendees[:5])}{"..." if len(attendees) > 5 else ""} |
| **Recurrence** | {meeting.get("recurrence", "none").capitalize()} |
| **Has Agenda** | {"Yes" if meeting.get("has_agenda") else "No"} |
| **Has Action Items** | {"Yes" if meeting.get("has_action_items") else "No"} |
| **Could Be Email** | {"Yes" if meeting.get("could_be_email") else "No"} |

> *{meeting.get("description", "")}*

---

## Entropy Engine Results

| Metric | Score | Visual |
|---|---|---|
| **Waste Score** | {waste_score}/100 | `[{waste_bar}]` |
| **Probability of Necessity** | {necessity_prob}% | `[{necessity_bar}]` |

### Verdict

> **{classification}**

### Async Alternative

> {recommendation}

---

*SilentSpace Guardian v0.1.0 — Protecting calendars, one audit at a time.*
"""


def save_report(title: str, report: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s-]+", "_", slug).strip("_")
    output_path = REPORTS_DIR / f"{slug}_report.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python audit_meeting.py <meeting.json>", file=sys.stderr)
        sys.exit(1)

    meeting_path = sys.argv[1]
    bin_path, use_wsl = ensure_cobol_binary()
    meeting = load_meeting(meeting_path)
    waste_score, necessity_prob = score_meeting(meeting, bin_path, use_wsl)

    title = meeting.get("title", "Untitled Meeting")
    classification = classify_meeting(waste_score)
    recommendation = async_recommendation(meeting, waste_score)

    width = 62
    print()
    print("=" * width)
    print(f"  SilentSpace Guardian -- Meeting Audit")
    print("=" * width)
    print(f"  Meeting  : {title}")
    print(f"  Waste    : {waste_score}/100")
    print(f"  Necessity: {necessity_prob}%")
    print(f"  Verdict  : {classification}")
    print(f"  Async    : {recommendation}")
    print("=" * width)

    report = generate_report(meeting, waste_score, necessity_prob)
    output_path = save_report(title, report)
    print(f"\n  Report saved to: {output_path.relative_to(ROOT)}")
    print()


if __name__ == "__main__":
    main()
