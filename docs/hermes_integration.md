# Hermes Integration

Hermes is the adaptive edge of SilentSpace Guardian. It provides the natural
language interface, context management, and orchestration layer that sits above
the deterministic Python/COBOL core.

---

## Architecture Overview

```
Hermes (agent runtime)
    │
    ├─ python/hermes_meeting_tool.py   ← structured JSON in/out (CLI boundary)
    │       │
    │       └─ audit_meeting_data()    ← Python callable (in-process boundary)
    │               │
    │               └─ cobol/entropy_engine  ← COBOL binary (deterministic scorer)
    │
    └─ skills/                         ← curated skill scaffolds for Hermes
```

**The Python/COBOL pipeline is the stable core.** It does not change to
accommodate Hermes. Hermes adapts to the pipeline.

**Hermes is the adaptive edge.** It handles unstructured input, context,
and orchestration. It does not touch the scoring logic.

---

## The Tool Boundary

### Option A — Python callable (in-process)

The cleanest integration path. Call `audit_meeting_data()` directly:

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
        "description": "Weekly sync to align on our alignment.",
    }
)

print(result["waste_score"])       # 92
print(result["necessity_prob"])    # 8
print(result["classification"])    # Corporate Heat Death Event: ...
print(result["recommendation"])    # Cancel and initiate a post-mortem...
```

No file I/O. No side effects. No console output. The `memory_context`
parameter is accepted but unused — reserved for future Hermes context passing.

### Option B — subprocess CLI (out-of-process)

Use `python/hermes_meeting_tool.py` when Hermes runs in a separate process
or when you need structured JSON output:

```bash
# From file:
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json

# From stdin:
cat meetings/weekly_alignment_sync.json | python python/hermes_meeting_tool.py --stdin

# With report generation:
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json --write-report
```

**JSON output (stdout):**

```json
{
  "title": "Weekly Alignment Sync",
  "waste_score": 92,
  "necessity_prob": 8,
  "classification": "Corporate Heat Death Event: Entropy Made Flesh — This meeting is why people quit.",
  "recommendation": "Cancel and initiate a post-mortem on how this ended up on six calendars.",
  "meeting": { ... }
}
```

With `--write-report`, the output also includes:

```json
{
  ...,
  "report_path": "reports/weekly_alignment_sync_report.md"
}
```

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | File not found or I/O error |
| 2 | JSON parse error |
| 3 | Meeting validation error (missing or invalid fields) |

---

## SOUL.md as the Persona Contract

[SOUL.md](../SOUL.md) defines the Guardian's persona and behavioral directives.
Hermes must honor them:

- **Classify before commenting** — run the audit before forming any opinion
- **Score before summarizing** — no summary without a score
- **Preserve evidence** — do not discard input data when reporting results
- **Prefer brevity over reassurance** — findings are stated, not softened
- **Recommendations must reduce organizational entropy** — not manage feelings
- **Never manufacture optimism** — if it scored 94, say 94

SOUL.md is not optional for Hermes. An agent that softens a 94/100 waste score
to "a high score that may warrant attention" has violated the contract.

---

## Example Hermes Prompts

These illustrate how Hermes should be invoked — not what to say verbatim.

**Audit a single meeting:**

> Audit this meeting. Return the waste score, necessity probability, classification, and recommended async alternative.
> [meeting JSON]

**Batch audit with summary:**

> Run all meetings in meetings/ through the audit pipeline. Generate the daily digest.

**Preflight check:**

> Scan the meeting list and flag any async candidates before the day begins.

**Interpret a score:**

> The entropy engine returned waste_score=87. What classification does that correspond to, and what is the recommended action?

---

## What Hermes Does Not Do

- Does not modify waste scores or classification labels
- Does not call external APIs (no calendar, no Slack, no email)
- Does not authenticate to any service
- Does not write to a database
- Does not generate its own skill definitions
- Does not override SOUL.md directives

See [docs/local_agent_setup.md](local_agent_setup.md) for runtime configuration.
See [skills/README.md](../skills/README.md) for the skill catalog.
