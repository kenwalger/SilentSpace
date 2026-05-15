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
├── ARCHITECTURE.md            # Visual architecture with Mermaid.js diagrams
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
│   ├── architecture.md        # Prose architecture and scoring formula
│   └── windows-wsl-setup.md  # Beginner setup guide for Windows + WSL2
├── meetings/                  # 12 mocked meeting JSON files
├── python/
│   ├── audit_meeting.py       # Single-meeting audit — compiles COBOL, runs pipeline, writes report
│   ├── audit_all_meetings.py  # Batch audit — all meetings + summary report
│   └── classify.py            # Classification tiers and async recommendations
└── reports/                   # Generated Markdown audit reports (gitignored)
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full technical breakdown,
including the COBOL scoring formula and meeting JSON schema.

---

*SilentSpace Guardian v0.1.0 — Protecting calendars, one audit at a time.*
