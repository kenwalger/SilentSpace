# Skill: cobol_output_interpreter

**Status:** Human-authored scaffold
**Constraint:** SOUL.md — preserve evidence, do not reinterpret deterministic output

---

## Purpose

Parse and contextualize the raw two-line output from the COBOL entropy engine
(`cobol/entropy_engine`). Given a raw stdout string, return structured integers
for `waste_score` and `necessity_prob`, and confirm that the output is valid.

This skill exists to document the COBOL interface contract explicitly. In normal
use, `score_meeting()` in `python/audit_meeting.py` handles this parsing. Use
this skill when debugging the engine directly, testing with custom inputs, or
verifying binary output in an agent context.

---

## When to Use

- When running the COBOL binary directly (bypassing Python) and needing to interpret output
- When debugging unexpected scores and needing to isolate the COBOL layer
- When writing agent tooling that calls the binary directly rather than via `audit_meeting_data()`
- When verifying that a compiled binary matches the expected formula

Do not use this skill to reinterpret or adjust scores. The COBOL output is
deterministic and authoritative. If the score is unexpected, check the input
values — not the output.

---

## Expected Inputs

Raw stdout from the COBOL entropy engine: two lines, each an integer.

```
095
005
```

Or as a Python string: `"095\n005\n"`.

The six stdin values the engine expects (one per line):

| Line | Parameter | Example |
|---|---|---|
| 1 | `duration_minutes` | `60` |
| 2 | `attendee_count` | `6` |
| 3 | `has_agenda` (0 or 1) | `0` |
| 4 | `has_action_items` (0 or 1) | `0` |
| 5 | `could_be_email` (0 or 1) | `1` |
| 6 | `recurrence_level` (0–4) | `3` |

---

## Expected Outputs

```python
{
    "waste_score": 92,    # int, 0–100
    "necessity_prob": 8   # int, 5–100; always max(5, 100 - waste_score)
}
```

---

## Invocation

**Direct binary call (Linux/macOS/WSL):**

```bash
printf "60\n6\n0\n0\n1\n3\n" | ./cobol/entropy_engine
```

Expected output for the Weekly Alignment Sync:
```
092
008
```

**Via Python `score_meeting()`:**

```python
import sys
sys.path.insert(0, "python")
from audit_meeting import ensure_cobol_binary, score_meeting

bin_path, wsl_prefix = ensure_cobol_binary()
waste_score, necessity_prob = score_meeting(meeting_dict, bin_path, wsl_prefix)
```

**Parsing raw output manually:**

```python
lines = raw_stdout.strip().splitlines()
waste_score = int(lines[0].strip())
necessity_prob = int(lines[1].strip())
```

---

## Guardrails

- Do not modify the parsed integers. The COBOL engine is the single source of truth for scoring.
- Do not call the binary with fewer or more than 6 stdin values. The binary will produce incorrect output silently.
- `waste_score` is clamped to [0, 100] by the COBOL binary. If you receive a value outside this range, the binary is not functioning correctly.
- `necessity_prob` must equal `max(5, 100 - waste_score)`. If it does not, the binary is not functioning correctly.
- This skill does not recompile the binary. If the binary is missing or corrupt, use `ensure_cobol_binary()` in `python/audit_meeting.py`.

---

## Tone Notes (SOUL.md)

COBOL output is not interpreted. It is reported. A waste score of 94 is 94.
An agent using this skill must not soften, round, or contextually reframe the
output. The number is the finding. The finding stands.

See [SOUL.md](../../SOUL.md) for the full behavioral contract.
