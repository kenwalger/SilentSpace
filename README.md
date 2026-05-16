# SilentSpace Guardian

> *"The most productive meeting is the one that never happens."*
> — Someone who had back-to-back syncs until 6 PM on a Friday

SilentSpace Guardian is an AI-powered anti-meeting auditor. It reads structured meeting data,
pipes it through a battle-tested COBOL entropy scoring engine, and generates authoritative
Markdown reports classifying each meeting on the Waste-Necessity Spectrum™.

No meeting is safe. Especially yours.

> "Because modern LLMs are too polite to tell your manager that a 12-person daily sync is a crime against engineering velocity, we outsourced the judgment to legacy mainframes."

---

## Quick Start

### Prerequisites

- Python 3.9+
- GnuCOBOL (`cobc`) — the entropy engine compiler
  - macOS: `brew install gnu-cobol`
  - Ubuntu/Debian: `sudo apt install gnucobol`
  - Windows: WSL with Ubuntu is detected and used automatically if `cobc`
    is not on the native PATH. Install via WSL: `sudo apt install gnucobol`
  - **Windows step-by-step:** see [docs/windows-wsl-setup.md](docs/windows-wsl-setup.md)

### First Run

```bash
python python/audit_meeting.py meetings/weekly_alignment_sync.json
```

The first run compiles the COBOL entropy engine automatically. Reports are saved to `reports/`.

### Batch Audit — All Meetings

```bash
python python/audit_all_meetings.py
```

Scores every file in `meetings/`, writes individual reports to `reports/`,
and produces a summary report at `reports/summary_report.md` with aggregate
stats, verdict breakdown, top offenders, and most common failure mode.

### Single Meeting

```bash
python python/audit_meeting.py meetings/weekly_alignment_sync.json
```

### Verify the Full Demo

Confirms compilation, scoring, and report generation all work end-to-end:

```bash
bash scripts/verify_demo.sh
```

The script detects your platform, compiles the COBOL engine (or confirms WSL fallback on Windows), audits one meeting with full output shown, runs the batch silently, and verifies all reports were written. On Windows, run from Git Bash. Expected output ends with:

```
==========================================
All 8 checks passed. The demo is ready.
```

If `cobc` is missing on Linux, macOS, or WSL, the script exits with a platform-appropriate install command rather than silently passing.

### Run Tests

```bash
pytest tests/
```

Tests cover the `audit_meeting_data()` agent interface before Hermes is wired in: return structure, score bounds (`waste_score` 0–100, `necessity_prob` 5–100), formula correctness (`necessity_prob = max(5, 100 − waste_score)`), classification and recommendation determinism, `ValueError` on missing required fields, and `SystemExit(1)` when no COBOL binary can be found or compiled.

These tests exist to establish a verified baseline for the agent tool boundary before integration begins.

---

## What It Does

**Single audit** (`audit_meeting.py`):
1. Reads a meeting JSON file from `meetings/`
2. Extracts six scoring parameters
3. Passes them to the COBOL entropy engine (`cobol/entropy_engine`)
4. COBOL returns a `waste_score` and `necessity_probability`
5. Python classifies the meeting and generates an async recommendation
6. A Markdown audit report is written to `reports/`

**Batch audit** (`audit_all_meetings.py`):
1. Runs every JSON file in `meetings/` through the same pipeline
2. Generates all individual reports
3. Writes `reports/summary_report.md` with aggregate statistics,
   verdict breakdown, top offenders, and most common failure mode

---

## Meeting Classifications

| Waste Score | Classification |
|---|---|
| 0–20 | Rare Gem: Genuine Human Interaction |
| 21–40 | Marginally Justified: Could Be a Loom |
| 41–60 | Calendar Debris: Occupies Space, Creates Little |
| 61–80 | Meeting-Shaped Void: Time's Natural Enemy |
| 81–100 | Corporate Heat Death Event: Entropy Made Flesh |

---

## Project Layout

```
silentspace-guardian/
├── .env                       # Local env overrides — gitignored
├── .gitignore
├── example.env                # Committed env variable reference
├── ARCHITECTURE.md            # Architecture signpost — three-layer summary, links to docs/
├── CHANGELOG.md
├── CLAUDE.md                  # Claude Code operational guide
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.md                 # MIT
├── README.md
├── SECURITY.md
├── cobol/
│   └── entropy_engine.cob     # Waste scoring algorithm (GnuCOBOL)
├── docs/
│   ├── architecture.md        # Prose architecture, scoring formula, agent boundary
│   ├── memory_model.md        # Memory planning doc for future Hermes integration
│   ├── scoring_model.md       # COBOL engine inputs, outputs, and formula rationale
│   └── windows-wsl-setup.md  # Beginner setup guide for Windows + WSL2
├── meetings/                  # Mocked meeting JSON files
├── scripts/
│   └── verify_demo.sh         # End-to-end verification script
├── tests/
│   ├── conftest.py            # sys.path setup for pytest
│   └── test_audit.py          # audit_meeting_data() pre-Hermes test suite
├── memory/
│   └── sample_meeting_history.json  # Sample prior-audit data (scaffolding)
├── python/
│   ├── audit_meeting.py       # Single-meeting audit + audit_meeting_data() agent interface
│   ├── audit_all_meetings.py  # Batch audit — all meetings + summary report
│   └── classify.py            # Classification tiers and async recommendations
└── reports/                   # Generated Markdown audit reports (gitignored)
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full technical breakdown,
including the agent tool boundary, meeting JSON schema, and constraint rationale.

See [docs/scoring_model.md](docs/scoring_model.md) for the COBOL engine reference:
inputs, outputs, formula rationale, and the intentional design of the stdin/stdout
interface.

---

## Current Status

SilentSpace Guardian v0.2.0-dev is a fully functional local auditing tool.

What works:

- Single-meeting audit via `python/audit_meeting.py` — reads a JSON file, runs the COBOL engine, classifies the result, writes a Markdown report
- Batch audit via `python/audit_all_meetings.py` — scores all 12 meetings, writes individual reports, and produces an aggregate summary report
- Auto-compilation of the COBOL entropy engine on first run (native or via WSL on Windows)
- `audit_meeting_data(meeting, memory_context=None) -> dict` — a clean, side-effect-free function that an agent can call directly without touching the CLI layer
- Cross-platform output: Windows console encoding fixed, path separators normalized, report slugs stable across punctuation in meeting titles
- Test suite (`tests/test_audit.py`) covering the agent tool boundary: return structure, score bounds, formula correctness, determinism, input validation, and graceful binary-missing failure

The scoring pipeline is deterministic. The COBOL formula is documented in `docs/scoring_model.md`. The entire system runs locally with no network access.

---

## Not Yet Implemented

The following are explicitly out of scope for this version:

- **Hermes integration** — no agent framework is wired in yet; `memory_context` is accepted but unused
- **Live calendar access** — no Google Calendar, Outlook, or CalDAV integration
- **OAuth or authentication** — no user accounts, no tokens, no external auth
- **Persistent memory** — `memory/sample_meeting_history.json` is scaffolding; no history is written back after audits
- **Slack, Teams, or email notifications** — reports are Markdown files only
- **Web application or REST API** — no server, no endpoints, no dashboard
- **Databases or cloud storage** — file system only
- **Docker or container infrastructure** — install prerequisites and run directly

These are not gaps — they are the designed boundary of v0.1.0 / v0.2.0-dev.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the road-to-production table.

---

## Next: Hermes Integration

The project is structured to support an agent-callable interface without any further refactoring. The function `audit_meeting_data(meeting, memory_context=None) -> dict` in `python/audit_meeting.py` is the intended tool boundary.

An agent (Hermes or any other framework) can call it directly:

```python
import sys
sys.path.insert(0, "python")
from audit_meeting import audit_meeting_data

result = audit_meeting_data(
    meeting={
        "title": "Weekly Alignment Sync",
        "recurrence": "weekly",
        "duration_minutes": 60,
        "attendees": ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"],
        "has_agenda": False,
        "has_action_items": False,
        "could_be_email": True,
        "organizer": "alice@corp.com",
        "description": "The one that outlived the team that created it.",
    }
)
# result["waste_score"]    → int
# result["necessity_prob"] → int
# result["classification"] → str
# result["recommendation"] → str
# result["meeting"]        → dict (original input)
```

No file I/O. No console output. No side effects. The `memory_context` parameter is the reserved slot for conversation history, prior audit results, and user preferences — the scaffolding is in place; the wiring is next.

See [docs/memory_model.md](docs/memory_model.md) for the planned memory data shape and longitudinal scoring approach.

---

*SilentSpace Guardian v0.2.0-dev — Protecting calendars, one audit at a time.*
