#!/usr/bin/env python3
"""
SilentSpace Guardian — Meeting Audit Engine

Reads a meeting JSON, runs it through the COBOL entropy scorer,
classifies the result, and writes a Markdown report to reports/.

Usage:
    python python/audit_meeting.py meetings/weekly_alignment_sync.json
"""

import functools
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from classify import async_recommendation, classify_meeting

# Windows console defaults to CP1252/CP437 and can't display the em-dash in
# classification labels. Reconfigure stdout to UTF-8 so the verdict prints cleanly.
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


def _get_wsl_prefix() -> list[str]:
    """Return a wsl command prefix using the first distro that has cobc."""
    for distro in ("Ubuntu", "Debian"):
        r = subprocess.run(
            ["wsl", "-d", distro, "--", "which", "cobc"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            return ["wsl", "-d", distro, "--"]
    return ["wsl", "--"]


def _compile(wsl_prefix: list[str]) -> None:
    """Compile entropy_engine.cob. Uses WSL if wsl_prefix is non-empty."""
    if wsl_prefix:
        print("Compiling COBOL entropy engine via WSL...")
        cmd = wsl_prefix + [
            "cobc", "-x", "-o", _to_wsl_path(COBOL_BIN), _to_wsl_path(COBOL_SRC),
        ]
    else:
        print("Compiling COBOL entropy engine...")
        cmd = ["cobc", "-x", "-o", str(COBOL_BIN), str(COBOL_SRC)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("COBOL compilation failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("Compilation successful.\n")


@functools.lru_cache(maxsize=1)
def ensure_cobol_binary() -> tuple[Path, list[str]]:
    """Return (bin_path, run_prefix). Compiles if the binary is absent.

    run_prefix is [] for native execution or ["wsl", "-d", distro, "--"]
    when the binary is a Linux ELF that must be invoked via WSL.
    """
    if COBOL_BIN_WIN.exists():
        return COBOL_BIN_WIN, []

    if COBOL_BIN.exists():
        # On Windows the existing binary is a Linux ELF compiled by WSL.
        if sys.platform == "win32":
            return COBOL_BIN, _get_wsl_prefix()
        return COBOL_BIN, []

    if shutil.which("cobc"):
        _compile([])
        return (COBOL_BIN_WIN if COBOL_BIN_WIN.exists() else COBOL_BIN), []

    if shutil.which("wsl"):
        prefix = _get_wsl_prefix()
        _compile(prefix)
        return COBOL_BIN, prefix

    print(
        "ERROR: GnuCOBOL (cobc) not found.\n"
        "  macOS  : brew install gnu-cobol\n"
        "  Linux  : sudo apt install gnucobol\n"
        "  Windows: install WSL then: sudo apt install gnucobol",
        file=sys.stderr,
    )
    sys.exit(1)


def load_meeting(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score_meeting(meeting: dict, bin_path: Path, wsl_prefix: list[str]) -> tuple[int, int]:
    """Pipe meeting parameters to the COBOL binary and parse the two-line output."""
    stdin_data = "\n".join([
        str(meeting.get("duration_minutes", 60)),
        str(len(meeting.get("attendees", []))),
        "1" if meeting.get("has_agenda", False) else "0",
        "1" if meeting.get("has_action_items", False) else "0",
        "1" if meeting.get("could_be_email", False) else "0",
        str(RECURRENCE_LEVELS.get(meeting.get("recurrence", "none"), 0)),
    ]) + "\n"

    cmd = (wsl_prefix + [_to_wsl_path(bin_path)]) if wsl_prefix else [str(bin_path)]
    result = subprocess.run(cmd, input=stdin_data, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Entropy engine error:\n{result.stderr}")

    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        raise ValueError(f"Unexpected entropy engine output: {result.stdout!r}")

    return int(lines[0].strip()), int(lines[1].strip())


def audit_meeting_data(
    meeting: dict,
    memory_context: Optional[dict] = None,
) -> dict:
    """Score and classify a meeting dict without reading from a file.

    This is the callable boundary for agent integration. Accepts a meeting
    dictionary and returns a structured result. memory_context is accepted
    but unused; reserved for future agent integration.

    Returns:
        {
            "title": str,
            "waste_score": int,
            "necessity_prob": int,
            "classification": str,
            "recommendation": str,
            "meeting": dict,
        }
    """
    bin_path, wsl_prefix = ensure_cobol_binary()
    waste_score, necessity_prob = score_meeting(meeting, bin_path, wsl_prefix)
    classification = classify_meeting(waste_score)
    recommendation = async_recommendation(meeting, waste_score)

    return {
        "title": meeting.get("title", "Untitled Meeting"),
        "waste_score": waste_score,
        "necessity_prob": necessity_prob,
        "classification": classification,
        "recommendation": recommendation,
        "meeting": meeting,
    }


def generate_report(
    meeting: dict,
    waste_score: int,
    necessity_prob: int,
    classification: str,
    recommendation: str,
) -> str:
    title = meeting.get("title", "Untitled Meeting")
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
    slug = re.sub(r"[^\w\s-]", " ", title.lower())
    slug = re.sub(r"[\s-]+", "_", slug).strip("_")
    output_path = REPORTS_DIR / f"{slug}_report.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python audit_meeting.py <meeting.json>", file=sys.stderr)
        sys.exit(1)

    meeting = load_meeting(sys.argv[1])
    result = audit_meeting_data(meeting)

    width = 62
    print()
    print("=" * width)
    print("  SilentSpace Guardian -- Meeting Audit")
    print("=" * width)
    print(f"  Meeting  : {result['title']}")
    print(f"  Waste    : {result['waste_score']}/100")
    print(f"  Necessity: {result['necessity_prob']}%")
    print(f"  Verdict  : {result['classification']}")
    print(f"  Async    : {result['recommendation']}")
    print("=" * width)

    report = generate_report(
        result["meeting"],
        result["waste_score"],
        result["necessity_prob"],
        result["classification"],
        result["recommendation"],
    )
    output_path = save_report(result["title"], report)
    print(f"\n  Report saved to: {output_path.relative_to(ROOT).as_posix()}")
    print()


if __name__ == "__main__":
    main()
