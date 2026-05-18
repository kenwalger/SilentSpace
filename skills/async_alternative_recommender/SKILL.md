# Skill: async_alternative_recommender

**Status:** Human-authored scaffold
**Constraint:** SOUL.md — recommendations must reduce organizational entropy

---

## Purpose

Given a scored meeting result, return the appropriate async alternative
recommendation. The recommendation is deterministic: same meeting title
always produces the same recommendation. No randomness. No LLM inference.

This skill wraps `async_recommendation()` from `python/classify.py`. It
exists as a named skill so that agent orchestration can call it explicitly
when the recommendation step needs to be separated from the scoring step.

In most workflows, `meeting_entropy_audit` already includes the recommendation.
Use this skill only when you need the recommendation independently.

---

## When to Use

- When you have a `waste_score` and a meeting dict but need only the recommendation
- When composing a digest or summary and want to re-derive recommendations from stored scores without re-running the full pipeline
- When auditing recommendation consistency across a batch of meetings

Do not use this skill to generate free-form advice about a meeting. The
recommendation pool is fixed and intentional. The Guardian does not improvise.

---

## Expected Inputs

```python
{
    "meeting": {
        "title": "string",   # required — used to seed the deterministic selector
        ...                  # other fields ignored by this skill
    },
    "waste_score": 75        # int, 0–100
}
```

---

## Expected Outputs

A single string from the fixed recommendation pool in `python/classify.py`.

Example:

```
"Cancel immediately. Send a Slack summary of what was going to be discussed."
```

The recommendation bucket is determined by waste score:

| Waste Score | Bucket |
|---|---|
| 0–20 | `none` |
| 21–40 | `low` |
| 41–60 | `medium` |
| 61–80 | `high` |
| 81–100 | `critical` |

Within each bucket, the specific recommendation is chosen by the MD5 hash
of the meeting title. It does not change between runs.

---

## Invocation

**Python (direct call):**

```python
import sys
sys.path.insert(0, "python")
from classify import async_recommendation

recommendation = async_recommendation(meeting_dict, waste_score)
```

**Via full audit (recommended for most cases):**

```python
from audit_meeting import audit_meeting_data
result = audit_meeting_data(meeting_dict)
recommendation = result["recommendation"]
```

---

## Guardrails

- Do not override or rephrase the recommendation text. It is fixed by design.
- Do not call this skill if `waste_score` is not yet available. Score first.
- Do not use this skill to generate alternative recommendations through LLM inference. The recommendations are from `classify.py`, not from a language model.
- If the waste score changes (e.g., due to a data correction), re-derive the recommendation rather than reusing a cached value.

---

## Tone Notes (SOUL.md)

Recommendations from this skill are direct and final. They do not hedge.
When surfacing a recommendation to a user or in a report, present it as
stated — do not soften, qualify, or expand it with encouraging language.

"Cancel immediately" means cancel immediately. Not "consider cancelling."
Not "it might be worth exploring alternatives." Cancel. Immediately.

See [SOUL.md](../../SOUL.md) for the full behavioral contract.
