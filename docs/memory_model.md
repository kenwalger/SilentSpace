# SilentSpace Guardian — Memory Model

*Planning document for persistent agent memory. Nothing here is wired into
scoring yet. This describes what will be implemented when Hermes is integrated.*

---

## Why Memory Is the Differentiator

Without memory, every audit is a fresh judgment on a frozen JSON file. The
COBOL engine is deterministic by design: the same inputs always produce the
same score. A meeting that scored 92 last quarter and 92 this quarter looks
identical to the engine, even if it has been reformed, cancelled and restarted,
or quietly expanded to twelve attendees.

Memory turns the auditor into an organizational observer. It makes three things
possible that are otherwise impossible:

1. **Trend detection** — a meeting's waste score over time reveals whether an
   intervention worked, whether a meeting is drifting, or whether it has been
   stable long enough to be trusted.

2. **Recurrence context** — the engine already penalizes recurrence by frequency.
   Memory adds longitudinal recurrence: a meeting that has existed for three
   years, unchanged, with no recorded outcomes, is not the same as a new weekly
   that has been running for a month.

3. **User preference context** — different users have different thresholds. A
   manager running a team of twelve has different meeting norms than a solo IC.
   Memory lets the agent calibrate recommendations to the person, not just the
   meeting.

---

## What Meeting History Should Remember

Each prior audit record should capture enough to answer two questions:
"What was this meeting's state then?" and "Did anything change?"

### Proposed Meeting History Shape

```json
{
  "meeting_id": "weekly_alignment_sync",
  "title": "Weekly Alignment Sync",
  "audit_history": [
    {
      "audited_at": "2026-02-01",
      "waste_score": 96,
      "necessity_prob": 4,
      "classification": "Corporate Heat Death Event: Entropy Made Flesh",
      "recommendation": "Declare a calendar emergency. Block this timeslot for silent, focused work.",
      "snapshot": {
        "duration_minutes": 60,
        "attendee_count": 8,
        "recurrence": "weekly",
        "has_agenda": false,
        "has_action_items": false,
        "could_be_email": true
      }
    },
    {
      "audited_at": "2026-05-15",
      "waste_score": 92,
      "necessity_prob": 8,
      "classification": "Corporate Heat Death Event: Entropy Made Flesh",
      "recommendation": "Declare a calendar emergency. Block this timeslot for silent, focused work.",
      "snapshot": {
        "duration_minutes": 60,
        "attendee_count": 6,
        "recurrence": "weekly",
        "has_agenda": false,
        "has_action_items": false,
        "could_be_email": true
      }
    }
  ],
  "notes": "Attendee count dropped from 8 to 6 between audits. Score improved by 4 points. Still a heat death event."
}
```

Fields that matter most:
- `meeting_id` — stable slug that survives title changes
- `audited_at` — ISO date; enables trend calculation
- `snapshot` — the six COBOL inputs at audit time; allows score re-derivation and diff
- `notes` — free-text observations; the only field an agent would write narratively

---

## User Preference Entries

Stored in `memory/USER.md`. Loaded as `memory_context["user"]` when passed to
`audit_meeting_data`. Not yet implemented.

```markdown
---
name: User Preferences
type: user
---

- Acceptable meeting duration: 30 minutes or less for status syncs
- Recurrence tolerance: weekly is acceptable for team standups, not for alignment syncs
- Attendee threshold: flags anything above 5 as likely over-invited
- Preferred recommendation style: blunt — skip the diplomatic framing
- Org context: IC on a 7-person team; no direct reports
```

The agent uses these to modulate the recommendation string returned by
`audit_meeting_data`, not the waste score. The COBOL score stays deterministic.
User context shapes what to say about it.

---

## Meeting History Entries

Stored in `memory/meeting_history.json`. Loaded as
`memory_context["history"][meeting_id]` when passed to `audit_meeting_data`.
Not yet implemented.

Example entry that would surface in a recommendation:

```markdown
---
name: Weekly Alignment Sync — Audit History
type: project
---

Audited 2026-02-01: score 96/100. Recommendation issued: cancel.
Audited 2026-05-15: score 92/100. Attendees reduced from 8 to 6.

Trend: marginal improvement. Meeting has existed since Q3 2019.
Classification has not changed across two audits.

How to apply: when generating a recommendation, note that prior
intervention reduced attendees but did not change the verdict.
A second recommendation should acknowledge the partial response
and escalate: the structural issues (no agenda, no actions,
could be email) were not addressed.
```

---

## How Recurring Meetings Could Earn a Longitudinal Penalty

The COBOL engine penalizes recurrence by frequency (weekly = level 3, +15
points). It has no concept of age. A meeting that has been weekly for five
years with no recorded outcomes scores the same as a meeting in its second
week.

When `memory_context["history"]` is available, `audit_meeting_data` could
apply an additional penalty before returning the result:

```
if meeting has 3+ audit records with no score improvement:
    apply longevity surcharge (suggested: +5, capped so total stays ≤ 100)
```

This would not change the COBOL binary. It would be a post-processing
adjustment in Python, applied only when history is present. The score
returned in the result dict would reflect it; the `memory_context` key
would be included in the result so the caller knows the adjustment was made.

This is not implemented. The `memory_context` parameter exists so the
function signature is stable when it is.

---

## What Is Implemented Now vs Planned Later

| Capability | Status |
|---|---|
| Deterministic COBOL scoring | Implemented |
| Classification tiers | Implemented |
| Async recommendations | Implemented |
| `audit_meeting_data(meeting, memory_context)` signature | Implemented |
| `memory_context` consumed by scoring | Planned |
| Meeting history file (`memory/meeting_history.json`) | Scaffolded (sample only) |
| User preference file (`memory/USER.md`) | Planned |
| Longitudinal recurrence penalty | Planned |
| Trend-aware recommendation text | Planned |
| Memory written back after each audit | Planned |

---

*The score is objective. The context is not. Memory is where the two meet.*
