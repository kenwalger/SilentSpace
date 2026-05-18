# SilentSpace Guardian

> *"The most productive meeting is the one that never happens."*
> — Someone who had back-to-back syncs until 6 PM on a Friday

SilentSpace Guardian is an AI-powered anti-meeting auditor. It reads structured meeting data,
pipes it through a battle-tested COBOL entropy scoring engine, and generates authoritative
Markdown reports classifying each meeting on the Waste-Necessity Spectrum™.

No meeting is safe. Especially yours.

> "Because modern LLMs are too polite to tell your manager that a 12-person daily sync is a crime against engineering velocity, we outsourced the judgment to legacy mainframes."

SilentSpace is a local-first AI meeting audit system. It uses a compiled COBOL entropy engine
for deterministic scoring, a Python orchestration layer for classification and reporting, and
Hermes as the adaptive agent edge for natural language interaction and scheduled workflows.

---

## Current Status

**v0.3.0-dev** — Hermes tool boundary implemented. Scheduled audits operational.

What works:

- Single-meeting audit via `python/audit_meeting.py` — reads JSON, runs COBOL engine, classifies, writes report
- Batch audit via `python/audit_all_meetings.py` — scores all 12 meetings, writes individual reports and aggregate summary
- Hermes agent tool boundary via `python/hermes_meeting_tool.py` — structured JSON in/out, file and stdin modes, optional report writing
- Three scheduled audit workflows: daily regret audit, weekly entropy summary, morning preflight
- Auto-compilation of the COBOL entropy engine on first run (native or via WSL on Windows)
- `audit_meeting_data(meeting, memory_context=None) -> dict` — clean, side-effect-free callable for agent integration
- Test suite: 96 tests covering the full pipeline, Hermes tool boundary, validation, and error handling

---

## Quick Start

### Prerequisites

- Python 3.9+
- GnuCOBOL (`cobc`) — the entropy engine compiler
  - macOS: `brew install gnu-cobol`
  - Ubuntu/Debian: `sudo apt install gnucobol`
  - Windows: WSL with Ubuntu is detected and used automatically. Install via WSL: `sudo apt install gnucobol`
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

### Verify the Full Demo

```bash
bash scripts/verify_demo.sh
```

Confirms compilation, scoring, and report generation end-to-end. Run from Git Bash on Windows.

### Run Tests

```bash
pytest tests/
# or, if a globally-installed plugin interferes:
pytest tests/ -p no:celery
```

---

## Hermes Integration

Hermes is the adaptive edge: natural language interface, context management, and orchestration
on top of the deterministic Python/COBOL core. The stable core does not change for Hermes;
Hermes adapts to the core.

### Hermes Tool Boundary

`python/hermes_meeting_tool.py` is the structured CLI interface for agent consumption.
It outputs JSON to stdout and communicates errors to stderr with non-zero exit codes.

```bash
# File input
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json

# Stdin input
cat meetings/weekly_alignment_sync.json | python python/hermes_meeting_tool.py --stdin

# With Markdown report
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json --write-report
```

**Example output:**

```json
{
  "title": "Weekly Alignment Sync",
  "waste_score": 92,
  "necessity_prob": 8,
  "classification": "Corporate Heat Death Event: Entropy Made Flesh — This meeting is why people quit.",
  "recommendation": "Declare a calendar emergency. Block this timeslot for silent, focused work.",
  "meeting": { ... }
}
```

**Exit codes:** `0` success · `1` file/IO error · `2` JSON parse error · `3` validation error

For in-process Python integration, call `audit_meeting_data()` directly:

```python
import sys
sys.path.insert(0, "python")
from audit_meeting import audit_meeting_data

result = audit_meeting_data(meeting_dict)
# result["waste_score"], result["classification"], result["recommendation"], ...
```

See [docs/hermes_integration.md](docs/hermes_integration.md) for the full integration guide.
See [docs/local_agent_setup.md](docs/local_agent_setup.md) for Ollama, OpenRouter, and system prompt setup.

---

## SOUL.md — Persona and Behavior Contract

[SOUL.md](SOUL.md) is the behavioral contract for the Guardian and for Hermes.

The Guardian is not an assistant. It is an auditor. It classifies before commenting, scores
before summarizing, and does not manufacture optimism to soften findings. A meeting that
scores 94/100 scores 94/100. The record speaks.

Hermes must honor SOUL.md. Skills must honor SOUL.md. Any agent configuration that softens,
reframes, or apologizes for audit findings is out of contract.

---

## Scheduled Audits

Three recurring workflows are available as shell scripts. They are not installed automatically.

| Workflow | Schedule | Output | Script |
|---|---|---|---|
| Daily Regret Audit | Weekdays 5 PM | `reports/daily_digest.md` | `scripts/run_daily_regret_audit.sh` |
| Weekly Entropy Summary | Fridays 4 PM | `reports/weekly_entropy.md` | `scripts/run_weekly_entropy_summary.sh` |
| Morning Preflight | Weekdays 7 AM | `reports/preflight_report.md` | `scripts/run_preflight_audit.sh` |

**Manual run:**

```bash
bash scripts/run_daily_regret_audit.sh
bash scripts/run_weekly_entropy_summary.sh
bash scripts/run_preflight_audit.sh
```

See [docs/scheduled_audits.md](docs/scheduled_audits.md) for cron entries and Windows Task Scheduler setup.

---

## Skills

`skills/` contains curated capability scaffolds for Hermes. All skills are human-authored
and reviewed against SOUL.md before use. Random agent-generated skill definitions are not
allowed.

| Skill | Purpose |
|---|---|
| [meeting_entropy_audit](skills/meeting_entropy_audit/SKILL.md) | Full audit pipeline for a single meeting |
| [async_alternative_recommender](skills/async_alternative_recommender/SKILL.md) | Deterministic async alternative for a scored meeting |
| [summary_report_writer](skills/summary_report_writer/SKILL.md) | Markdown summary from a batch of audit results |
| [cobol_output_interpreter](skills/cobol_output_interpreter/SKILL.md) | Parse and contextualize raw COBOL engine output |

See [skills/README.md](skills/README.md) for the authorship policy and how SOUL.md constrains skill behavior.
See [docs/skills.md](docs/skills.md) for the full skill catalog with invocation examples.

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

## Testing

**96 tests** across two suites:

- `tests/test_audit.py` — `audit_meeting_data()` pre-Hermes baseline: return structure, score bounds, formula correctness, classification/recommendation determinism, input validation, binary-missing failure, CLI error handling, real meeting file schema conformance
- `tests/test_hermes_tool.py` — Hermes tool boundary: file input, stdin input, JSON output structure, all error paths and exit codes, `--write-report`

```bash
pytest tests/ -p no:celery -v
```

**Prerequisite:** GnuCOBOL (`cobc`) must be installed or the binary must already exist at `cobol/entropy_engine`. The wrapper auto-compiles on first use.

---

## Verification

```bash
# End-to-end pipeline
bash scripts/verify_demo.sh

# Hermes tool boundary
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json
cat meetings/weekly_alignment_sync.json | python python/hermes_meeting_tool.py --stdin
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json --write-report

# Scheduled audit scripts
bash scripts/run_daily_regret_audit.sh
bash scripts/run_weekly_entropy_summary.sh
bash scripts/run_preflight_audit.sh

# Full test suite
pytest tests/ -p no:celery
```

---

## Project Structure

```
silentspace-guardian/
├── CLAUDE.md                      # Claude Code operational guide
├── SOUL.md                        # Guardian persona and behavior contract
├── ARCHITECTURE.md                # Three-layer summary, links to docs/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE.md
├── cobol/
│   └── entropy_engine.cob         # Waste scoring algorithm (GnuCOBOL)
├── docs/
│   ├── architecture.md            # Full technical breakdown with Mermaid diagrams
│   ├── hermes_integration.md      # Tool boundary, SOUL.md contract, example prompts
│   ├── local_agent_setup.md       # GnuCOBOL install, Ollama, OpenRouter, system prompt
│   ├── memory_model.md            # Memory planning for future Hermes context
│   ├── scheduled_audits.md        # Cron setup, Windows Task Scheduler, what is mocked
│   ├── scoring_model.md           # COBOL engine inputs, outputs, formula rationale
│   ├── skills.md                  # Full skill catalog with invocation examples
│   └── windows-wsl-setup.md      # Beginner setup guide for Windows + WSL2
├── meetings/                      # Mocked meeting JSON files (12 meetings)
├── memory/
│   └── sample_meeting_history.json  # Sample prior-audit data (scaffolding)
├── python/
│   ├── audit_meeting.py           # Single-meeting audit + audit_meeting_data() agent interface
│   ├── audit_all_meetings.py      # Batch audit — all meetings + summary report
│   ├── classify.py                # Classification tiers and deterministic recommendations
│   ├── generate_daily_digest.py   # Daily regret audit helper → reports/daily_digest.md
│   ├── generate_preflight.py      # Morning preflight helper → reports/preflight_report.md
│   ├── generate_weekly_entropy.py # Weekly entropy helper → reports/weekly_entropy.md
│   └── hermes_meeting_tool.py     # Hermes agent tool boundary (JSON in/out CLI)
├── scripts/
│   ├── run_daily_regret_audit.sh  # Daily 5 PM regret audit
│   ├── run_preflight_audit.sh     # Morning 7 AM preflight
│   ├── run_weekly_entropy_summary.sh  # Friday 4 PM entropy summary
│   └── verify_demo.sh             # End-to-end verification
├── skills/
│   ├── README.md                  # Authorship policy, SOUL.md constraints
│   ├── async_alternative_recommender/SKILL.md
│   ├── cobol_output_interpreter/SKILL.md
│   ├── entropy_audit/SKILL.md     # Legacy — superseded by meeting_entropy_audit
│   ├── meeting_entropy_audit/SKILL.md
│   └── summary_report_writer/SKILL.md
└── tests/
    ├── conftest.py                # sys.path setup for pytest
    ├── test_audit.py              # audit_meeting_data() baseline suite (59 tests)
    └── test_hermes_tool.py        # hermes_meeting_tool.py suite (37 tests)
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full technical breakdown,
including Mermaid diagrams for the data flow, scoring pipeline, and module dependencies.

See [docs/scoring_model.md](docs/scoring_model.md) for the COBOL engine reference:
inputs, outputs, and formula rationale.

### Why COBOL?

Because deterministic systems still matter.

SilentSpace intentionally separates:
- probabilistic language reasoning (Hermes + LLMs)

from:
- deterministic scoring logic (GnuCOBOL).

The joke eventually became an architecture pattern.

---

## Not Yet Implemented

- **Live calendar access** — no Google Calendar, Outlook, or CalDAV integration
- **OAuth or authentication** — no user accounts, no tokens
- **Persistent memory** — `memory/sample_meeting_history.json` is scaffolding; no history written back
- **Slack, Teams, or email notifications** — reports are Markdown files only
- **Web application or REST API** — no server, no endpoints
- **Databases or cloud storage** — file system only

These are designed boundaries, not gaps.

---

*SilentSpace Guardian v0.3.0-dev — Protecting calendars, one audit at a time.*
