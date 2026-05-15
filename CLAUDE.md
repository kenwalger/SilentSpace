# CLAUDE.md — SilentSpace Guardian

## What This Is

SilentSpace Guardian is a humorous-but-functional meeting auditor. It reads meeting JSON files,
passes their key fields to a compiled COBOL entropy scoring binary, and generates Markdown reports
classifying each meeting by its organizational waste footprint.

## Key Workflow

1. Python reads a meeting JSON from `meetings/`
2. Python extracts 6 scoring parameters from the JSON
3. Python calls the compiled COBOL binary (`cobol/entropy_engine`) with those parameters as CLI args
4. COBOL returns two integers (waste_score, necessity_prob) on separate stdout lines
5. Python calls `python/classify.py` for a human-readable verdict and async recommendation
6. Python writes a Markdown report to `reports/<slug>_report.md`

## COBOL Compilation

The binary must be compiled before use. `audit_meeting.py` does this automatically on first run:

```bash
cobc -x -o cobol/entropy_engine cobol/entropy_engine.cob
```

On Windows the binary may be named `entropy_engine.exe`. The Python wrapper handles both.

## Meeting JSON Schema

Required fields:

| Field | Type | Description |
|---|---|---|
| `title` | string | Meeting name |
| `recurrence` | string | `"none"`, `"monthly"`, `"biweekly"`, `"weekly"`, `"daily"` |
| `duration_minutes` | int | Length of the meeting |
| `attendees` | list[string] | Attendee names or roles |
| `has_agenda` | bool | Was an agenda distributed beforehand? |
| `has_action_items` | bool | Are action items expected? |
| `could_be_email` | bool | Should this have been an email? |
| `organizer` | string | Who called this meeting |
| `description` | string | Flavor text |

## COBOL Notes

- `cobol/entropy_engine.cob` uses GnuCOBOL fixed-format syntax
- Accepts 6 positional CLI arguments (see `docs/architecture.md` for full formula)
- Outputs two integers on separate stdout lines: waste_score then necessity_prob
- All scoring is deterministic — same input always yields same output

## Scoring Formula (Summary)

```
waste_score = 20
            + min(30, (attendees - 3) × 2)    if attendees > 3
            + ((duration - 30) / 15) × 3      if duration > 30
            + recurrence_level × 5
            + 15 if no agenda
            + 10 if no action items
            + 20 if could_be_email
            [capped at 100]

necessity_prob = max(5, 100 - waste_score)
```

## What NOT to Build Yet

- No calendar integration (Google Calendar, Outlook, CalDAV)
- No Slack, Teams, or messaging integrations
- No OAuth or external authentication
- No web application, REST API, or database
- No Docker or container infrastructure
- No external API calls of any kind

## Tone

Dry enterprise satire throughout. The code must be real and runnable. The copy can be absurd.
The COBOL is not a joke — it compiles and produces correct output.
