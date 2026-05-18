# Skill: meeting_entropy_audit

**Status:** Human-authored scaffold
**Constraint:** SOUL.md — classify before commenting, score before summarizing

---

## Purpose

Run a single meeting through the full SilentSpace Guardian audit pipeline.
Produces a structured result containing a waste score, necessity probability,
classification tier, and async alternative recommendation.

This skill is the primary entry point for any agent that needs to assess a
single meeting. It does not generate opinions. It runs the scoring pipeline
and returns what the pipeline returns.

---

## When to Use

- When an agent receives a meeting JSON object and needs a scored audit result
- When Hermes needs to classify a meeting before deciding what to do next
- When building a report, digest, or summary that requires per-meeting scores
- When validating that a meeting JSON is well-formed before further processing

Do not use this skill to generate narrative commentary about a meeting without
first obtaining a score. The score comes first. Always.

---

## Expected Inputs

A meeting dictionary conforming to the SilentSpace meeting JSON schema:

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | Yes | Non-empty |
| `duration_minutes` | int | Yes | Positive integer |
| `attendees` | list[string] | Yes | Non-empty list |
| `recurrence` | string | No | `"none"` `"monthly"` `"biweekly"` `"weekly"` `"daily"` |
| `has_agenda` | bool | No | Defaults to `false` if absent |
| `has_action_items` | bool | No | Defaults to `false` if absent |
| `could_be_email` | bool | No | Defaults to `false` if absent |
| `organizer` | string | No | For reporting only |
| `description` | string | No | Flavor text for reports |

---

## Expected Outputs

A structured result dict (from `audit_meeting_data()`):

```json
{
  "title": "string",
  "waste_score": 0,
  "necessity_prob": 100,
  "classification": "string",
  "recommendation": "string",
  "meeting": {}
}
```

Or, via the CLI tool:

```json
{
  "title": "...",
  "waste_score": 92,
  "necessity_prob": 8,
  "classification": "Corporate Heat Death Event: Entropy Made Flesh — ...",
  "recommendation": "Cancel and initiate a post-mortem...",
  "meeting": { ... },
  "report_path": "reports/weekly_alignment_sync_report.md"
}
```

---

## Invocation

**Python (direct call):**

```python
import sys
sys.path.insert(0, "python")
from audit_meeting import audit_meeting_data

result = audit_meeting_data(meeting_dict)
```

**CLI (file input):**

```bash
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json
```

**CLI (stdin):**

```bash
cat meetings/weekly_alignment_sync.json | python python/hermes_meeting_tool.py --stdin
```

**CLI (with report):**

```bash
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json --write-report
```

---

## Guardrails

- Do not modify or reinterpret the `waste_score` or `necessity_prob` returned by the COBOL engine. These are deterministic outputs from a compiled binary. They are not suggestions.
- Do not call this skill on partial or incomplete meeting data. Validate first.
- Do not call this skill in a loop without checking exit codes (CLI) or catching `ValueError` (Python).
- This skill has no network access. It does not call any external API.
- This skill does not write files unless `--write-report` is explicitly passed.

---

## Tone Notes (SOUL.md)

The Guardian classifies. It does not comfort. When reporting results from this
skill, preserve the classification label verbatim. Do not soften it. A meeting
classified as a "Corporate Heat Death Event" is a Corporate Heat Death Event.
The record speaks. Do not apologize for it.

See [SOUL.md](../../SOUL.md) for the full behavioral contract.
