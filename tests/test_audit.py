"""
Pre-Hermes integration tests for audit_meeting_data().

These tests verify that the agent tool boundary holds before any agent
framework is wired in. They cover return structure, score bounds, formula
correctness, classification/recommendation determinism, input validation,
and graceful handling of a missing COBOL binary.

Run with:  pytest tests/
"""

import shutil
from pathlib import Path

import pytest

import audit_meeting
from audit_meeting import audit_meeting_data, ensure_cobol_binary


# ── Fixtures ──────────────────────────────────────────────────────────────────

# A minimal low-waste meeting: short, two people, agenda, action items, not email.
# Expected score: 20 (base) — no penalties apply.
_MINIMAL = {
    "title": "Pre-Hermes Test Meeting",
    "recurrence": "none",
    "duration_minutes": 30,
    "attendees": ["Alice", "Bob"],
    "has_agenda": True,
    "has_action_items": True,
    "could_be_email": False,
    "organizer": "alice@corp.com",
    "description": "Exists only to satisfy the entropy engine.",
}

# A maxed-out meeting: long, crowded, no agenda, no actions, could be email, weekly.
# Formula: 20 + 30 (attendee cap) + 18 (dur drag) + 15 (weekly) + 15 + 10 + 20 = 128 → capped at 100.
_HIGH_WASTE = {
    "title": "Synergy Touchpoint v3",
    "recurrence": "weekly",
    "duration_minutes": 120,
    "attendees": [f"Person{i}" for i in range(15)],
    "has_agenda": False,
    "has_action_items": False,
    "could_be_email": True,
    "organizer": "gone@corp.com",
    "description": "Third iteration of a meeting that should not have had a first.",
}


@pytest.fixture
def meeting():
    return dict(_MINIMAL)


@pytest.fixture
def high_waste_meeting():
    return dict(_HIGH_WASTE)


# ── Return structure ──────────────────────────────────────────────────────────

class TestReturnStructure:
    def test_returns_dict(self, meeting):
        assert isinstance(audit_meeting_data(meeting), dict)

    def test_has_all_required_keys(self, meeting):
        result = audit_meeting_data(meeting)
        for key in ("title", "waste_score", "necessity_prob", "classification", "recommendation", "meeting"):
            assert key in result, f"Missing key in result: {key!r}"

    def test_meeting_dict_is_passed_through(self, meeting):
        result = audit_meeting_data(meeting)
        assert result["meeting"] is meeting

    def test_title_matches_input(self, meeting):
        assert audit_meeting_data(meeting)["title"] == "Pre-Hermes Test Meeting"

    def test_memory_context_accepted_and_ignored(self, meeting):
        result = audit_meeting_data(meeting, memory_context={"history": [], "user": {}})
        assert isinstance(result, dict)


# ── Score bounds ──────────────────────────────────────────────────────────────

class TestScoreBounds:
    def test_waste_score_is_int(self, meeting):
        assert isinstance(audit_meeting_data(meeting)["waste_score"], int)

    def test_waste_score_lower_bound(self, meeting):
        score = audit_meeting_data(meeting)["waste_score"]
        assert score >= 0, f"waste_score {score} is below 0"

    def test_waste_score_upper_bound(self, meeting):
        score = audit_meeting_data(meeting)["waste_score"]
        assert score <= 100, f"waste_score {score} exceeds 100"

    def test_necessity_prob_is_int(self, meeting):
        assert isinstance(audit_meeting_data(meeting)["necessity_prob"], int)

    def test_necessity_prob_minimum_is_five(self, meeting):
        prob = audit_meeting_data(meeting)["necessity_prob"]
        assert prob >= 5, f"necessity_prob {prob} is below the floor of 5"

    def test_necessity_prob_maximum(self, meeting):
        assert audit_meeting_data(meeting)["necessity_prob"] <= 100

    def test_necessity_prob_formula(self, meeting):
        result = audit_meeting_data(meeting)
        expected = max(5, 100 - result["waste_score"])
        assert result["necessity_prob"] == expected

    def test_high_waste_meeting_scores_at_cap(self, high_waste_meeting):
        score = audit_meeting_data(high_waste_meeting)["waste_score"]
        assert score == 100, f"Expected waste_score 100 (capped), got {score}"

    def test_high_waste_meeting_necessity_at_floor(self, high_waste_meeting):
        prob = audit_meeting_data(high_waste_meeting)["necessity_prob"]
        assert prob == 5, f"Expected necessity_prob 5 (floor), got {prob}"


# ── Classification and recommendation ────────────────────────────────────────

class TestClassificationAndRecommendation:
    def test_classification_is_nonempty_string(self, meeting):
        c = audit_meeting_data(meeting)["classification"]
        assert isinstance(c, str) and c.strip()

    def test_recommendation_is_nonempty_string(self, meeting):
        r = audit_meeting_data(meeting)["recommendation"]
        assert isinstance(r, str) and r.strip()

    def test_classification_is_deterministic(self, meeting):
        c1 = audit_meeting_data(meeting)["classification"]
        c2 = audit_meeting_data(dict(meeting))["classification"]
        assert c1 == c2

    def test_recommendation_is_deterministic(self, meeting):
        r1 = audit_meeting_data(meeting)["recommendation"]
        r2 = audit_meeting_data(dict(meeting))["recommendation"]
        assert r1 == r2

    def test_high_waste_classification_label(self, high_waste_meeting):
        c = audit_meeting_data(high_waste_meeting)["classification"]
        assert "Corporate Heat Death Event" in c


# ── Input validation ──────────────────────────────────────────────────────────

class TestInputValidation:
    def test_missing_title_raises_valueerror(self, meeting):
        del meeting["title"]
        with pytest.raises(ValueError, match="title"):
            audit_meeting_data(meeting)

    def test_missing_duration_raises_valueerror(self, meeting):
        del meeting["duration_minutes"]
        with pytest.raises(ValueError, match="duration_minutes"):
            audit_meeting_data(meeting)

    def test_missing_attendees_raises_valueerror(self, meeting):
        del meeting["attendees"]
        with pytest.raises(ValueError, match="attendees"):
            audit_meeting_data(meeting)

    def test_empty_dict_error_message_lists_all_required_fields(self):
        with pytest.raises(ValueError) as exc_info:
            audit_meeting_data({})
        msg = str(exc_info.value)
        for field in ("title", "duration_minutes", "attendees"):
            assert field in msg, f"Expected {field!r} in error message: {msg!r}"

    @pytest.mark.parametrize("optional_field", [
        "has_agenda", "has_action_items", "could_be_email",
        "recurrence", "organizer", "description",
    ])
    def test_optional_field_absent_uses_default(self, meeting, optional_field):
        meeting.pop(optional_field, None)
        result = audit_meeting_data(meeting)
        assert isinstance(result["waste_score"], int)
        assert 0 <= result["waste_score"] <= 100


# ── COBOL binary missing ──────────────────────────────────────────────────────

class TestCobolBinaryMissing:
    """Verify that a missing COBOL binary fails with exit code 1, not silently."""

    def test_no_cobol_binary_exits_with_code_1(self, monkeypatch):
        # Clear the LRU cache so monkeypatched values are evaluated.
        ensure_cobol_binary.cache_clear()

        # Point binary paths to locations that will never exist.
        monkeypatch.setattr(audit_meeting, "COBOL_BIN",     Path("/no/such/entropy_engine"))
        monkeypatch.setattr(audit_meeting, "COBOL_BIN_WIN", Path("/no/such/entropy_engine.exe"))
        # Make shutil.which return None for every query (no cobc, no wsl).
        monkeypatch.setattr(audit_meeting.shutil, "which", lambda *_: None)

        with pytest.raises(SystemExit) as exc_info:
            ensure_cobol_binary()

        assert exc_info.value.code == 1

        # Restore the cache so any tests that run after this can recompile cleanly.
        ensure_cobol_binary.cache_clear()
