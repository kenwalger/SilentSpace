#!/usr/bin/env python3
"""
SilentSpace Guardian — Hermes Agent Tool Boundary

Accepts a meeting JSON (from a file path or --stdin) and outputs a structured
JSON result to stdout for consumption by Hermes or any other agent framework.

Usage:
    python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json
    cat meetings/weekly_alignment_sync.json | python python/hermes_meeting_tool.py --stdin
    python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json --write-report

Exit codes:
    0  success
    1  file not found or I/O error
    2  JSON parse error
    3  meeting validation error (missing/invalid fields)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).parent))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from audit_meeting import audit_meeting_data, generate_report, save_report


def _die(code: int, msg: str) -> NoReturn:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _load_file(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        _die(1, f"File not found: {path}")
    except OSError as exc:
        _die(1, str(exc))

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        _die(2, f"Invalid JSON in {path}: {exc}")


def _load_stdin() -> dict:
    try:
        raw = sys.stdin.read()
    except OSError as exc:
        _die(1, f"Failed to read from stdin: {exc}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        _die(2, f"Invalid JSON on stdin: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "SilentSpace Guardian — Hermes agent tool boundary.\n"
            "Outputs structured JSON to stdout."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="MEETING_JSON",
        help="Path to a meeting JSON file",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read meeting JSON from stdin instead of a file",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write a Markdown audit report to reports/ in addition to JSON output",
    )

    args = parser.parse_args()

    if args.stdin and args.file:
        parser.error("Specify a file path or --stdin, not both.")
    if not args.stdin and not args.file:
        parser.error("Specify a file path or use --stdin.")

    meeting = _load_stdin() if args.stdin else _load_file(args.file)

    if not isinstance(meeting, dict):
        _die(3, f"Meeting JSON must be an object, got {type(meeting).__name__}")

    try:
        result = audit_meeting_data(meeting)
    except ValueError as exc:
        _die(3, str(exc))

    output = {
        "title": result["title"],
        "waste_score": result["waste_score"],
        "necessity_prob": result["necessity_prob"],
        "classification": result["classification"],
        "recommendation": result["recommendation"],
        "meeting": result["meeting"],
    }

    if args.write_report:
        report = generate_report(
            result["meeting"],
            result["waste_score"],
            result["necessity_prob"],
            result["classification"],
            result["recommendation"],
        )
        report_path = save_report(result["title"], report)
        output["report_path"] = str(report_path)

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
