# SilentSpace Guardian — Scoring Model

The COBOL entropy engine is a deterministic quantization of corporate ambiguity.
Six inputs go in. Two integers come out. The same meeting always receives the
same verdict, because organizational waste is not a matter of interpretation.

---

## Inputs

The engine reads six values from stdin, one per line, in this order:

| Line | Field | Type | Notes |
|---|---|---|---|
| 1 | `duration_minutes` | integer | Total scheduled meeting length |
| 2 | `attendee_count` | integer | Number of people on the invite |
| 3 | `has_agenda` | 0 or 1 | 1 = an agenda was distributed beforehand |
| 4 | `has_action_items` | 0 or 1 | 1 = action items are expected from this meeting |
| 5 | `could_be_email` | 0 or 1 | 1 = this meeting is, at its core, an email |
| 6 | `recurrence_level` | 0–4 | none=0, monthly=1, biweekly=2, weekly=3, daily=4 |

Python maps the JSON meeting fields to these values and pipes them as a
newline-delimited string. The engine reads them with plain `ACCEPT` statements —
no argument parsing, no flags, no configuration.

---

## Outputs

Two integers on separate stdout lines:

| Line | Field | Range | Meaning |
|---|---|---|---|
| 1 | `waste_score` | 0–100 | Organizational entropy index |
| 2 | `necessity_prob` | 5–100 | Estimated probability the meeting needed to happen |

---

## Scoring Formula

### Base Score

Every meeting starts at **20**. This is not a neutral baseline. It reflects
the minimum entropy cost of gathering any number of people in a room, or its
digital equivalent.

### Attendee Bloat Penalty

```
if attendee_count > 3:
    penalty = min(30, (attendee_count - 3) × 2)
    waste_score += penalty
```

Three attendees is the threshold. Below that, it is a conversation. Above
that, the penalty accrues at 2 points per additional person, capped at 30.
A 3-person meeting adds nothing. An 18-person meeting hits the cap.

### Duration Drag Penalty

```
if duration_minutes > 30:
    waste_score += floor((duration_minutes - 30) / 15) × 3
```

The penalty applies only above 30 minutes. Meetings of 30 minutes or fewer
are at the floor: they pay no duration cost regardless of how long they
actually run. Above 30, the penalty increases in discrete 15-minute steps
at 3 points each.

**Why integer quantization?** Because the COBOL integer division is exact,
predictable, and honest about what it knows. A 44-minute meeting and a
45-minute meeting are not meaningfully different. The engine treats them as
the same tier and charges accordingly. Precision here would be false.

| Duration | Duration drag |
|---|---|
| ≤ 30 min | 0 |
| 31–45 min | 3 |
| 46–60 min | 6 |
| 61–75 min | 9 |
| 76–90 min | 12 |
| 91–105 min | 15 |

### Recurrence Tax

```
waste_score += recurrence_level × 5
```

A one-off meeting costs what it costs. A recurring meeting compounds. Daily
recurrence at level 4 adds 20 points — equivalent to the email crime penalty —
because a meeting that happens every day is either genuinely essential or a
structural failure that has been normalized.

| Recurrence | Level | Tax |
|---|---|---|
| None (one-off) | 0 | +0 |
| Monthly | 1 | +5 |
| Biweekly | 2 | +10 |
| Weekly | 3 | +15 |
| Daily | 4 | +20 |

### Behavioral Penalties

```
if has_agenda = 0:    waste_score += 15   # agendaless chaos premium
if has_action_items = 0: waste_score += 10   # actionless void surcharge
if could_be_email = 1:   waste_score += 20   # email crime penalty
```

These three flags capture the behavioral profile of the meeting. Together
they represent up to 45 points — nearly half the available range — because
process failures are more diagnostic than duration or attendance alone.

A meeting with an agenda is making a claim about its own purpose. A meeting
with expected action items is making a claim about its own value. A meeting
that could have been an email is making neither.

### Cap

```
waste_score = min(100, waste_score)
```

The score is bounded at 100. Some meetings exceed 100 under the formula
(Synergy Touchpoint v3 yields 106 uncapped). The cap is not forgiveness.
It is acknowledgement that after a point, additional precision is not useful.

---

## Outputs Explained

### Why `waste_score` Is the Primary Signal

`waste_score` is the output the rest of the system is built around. The
classification tiers, the summary report indicators, and the `memory_context`
longitudinal penalty are all keyed to it. It is a single number that can be
compared across meetings, trended over time, and sorted without ambiguity.

### Why `necessity_prob` Is Currently `100 - waste_score`

```
necessity_prob = max(5, 100 - waste_score)
```

This is a deliberate simplification. In the current implementation, necessity
is derived entirely from waste. They move in opposite directions on the same
axis. A meeting with a waste score of 60 has a necessity probability of 40%.

The 5% floor exists because the engine declines to declare any meeting
completely unnecessary. Even the most structurally catastrophic meeting might
serve a purpose the inputs cannot capture. The floor is not optimism. It is
epistemic humility encoded in a `max()` call.

In a future implementation with `memory_context`, necessity could be estimated
independently using historical outcomes, stated goals, and user preferences.
Until that work is done, `100 - waste_score` is accurate enough and honest
about its own limitations.

---

## Why stdin/stdout

The interface is intentionally simple. Python pipes six integers to the binary
and reads two integers back. No JSON, no flags, no protocol. This has two
consequences:

**Portability.** The binary can be tested directly from a terminal:

```bash
printf "60\n6\n0\n0\n1\n3\n" | ./cobol/entropy_engine
```

**Agent-friendliness.** `audit_meeting_data()` wraps the subprocess call
completely. An agent calling the function never touches the COBOL interface.
The stdin/stdout boundary is internal and invisible above the Python layer.

If the COBOL binary were replaced with a different implementation — a
different compiler, a different language, a different scoring model — nothing
outside `score_meeting()` in `audit_meeting.py` would need to change.

---

## The COBOL Layer Is Stateless and Unaware

The entropy engine knows nothing about the agent layer. It does not know what
called it, why, or what will be done with the result. It receives six integers
and emits two. It has no memory, no configuration, and no opinions about what
the numbers mean.

This is intentional. Keeping the scoring layer stateless and isolated means:

- The formula is auditable: the same inputs always produce the same outputs,
  with no hidden state affecting the result
- The COBOL binary can be tested and validated independently of any Python,
  agent, or memory logic
- Future changes to the agent layer (memory context, user preferences,
  longitudinal adjustments) happen in Python, not COBOL

The COBOL layer scores. The Python layer interprets. The agent layer decides.
These responsibilities do not cross.

---

## Formula Reference

```
waste_score = 20
            + min(30, (attendee_count − 3) × 2)    if attendee_count > 3
            + floor((duration_minutes − 30) / 15) × 3  if duration_minutes > 30
            + recurrence_level × 5
            + 15   if has_agenda = 0
            + 10   if has_action_items = 0
            + 20   if could_be_email = 1
            [capped at 100]

necessity_prob = max(5, 100 − waste_score)
```
