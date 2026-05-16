"""
Pre-Hermes integration tests for audit_meeting_data() and the CLI.

These tests verify that the agent tool boundary holds before any agent
framework is wired in. They cover return structure, score bounds, formula
correctness, classification/recommendation determinism, input validation
(presence, type, and shape), graceful handling of a missing COBOL binary,
clean CLI error output, and schema conformance of all committed meeting files.

Runtime dependency: 25 of 59 tests call audit_meeting_data() or score_meeting()
against the real COBOL entropy engine. GnuCOBOL (cobc) must be installed, or
the binary must already exist at cobol/entropy_engine. The Python wrapper
compiles it automatically on first use; a clean run on a machine with cobc will
compile once and cache the result for the session. The remaining 34 tests
(TestCobolBinaryMissing, TestCliErrorHandling, TestRealMeetingFiles, and all
TestInputValidation cases that raise before the binary is consulted) require no
COBOL binary.

Run with:  pytest tests/ -p no:celery
"""

import json
import subprocess
import sys
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
# Formula: 20 + 24 (attendee: min(30,(15-3)*2)) + 18 (dur drag) + 15 (weekly) + 15 + 10 + 20 = 122 → capped at 100.
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
    # Required-field presence
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

    # Title type/shape
    def test_title_empty_string_raises_valueerror(self, meeting):
        meeting["title"] = ""
        with pytest.raises(ValueError, match="title"):
            audit_meeting_data(meeting)

    def test_title_whitespace_only_raises_valueerror(self, meeting):
        meeting["title"] = "   "
        with pytest.raises(ValueError, match="title"):
            audit_meeting_data(meeting)

    def test_title_wrong_type_raises_valueerror(self, meeting):
        meeting["title"] = 42
        with pytest.raises(ValueError, match="title"):
            audit_meeting_data(meeting)

    # duration_minutes type/shape
    def test_duration_none_raises_valueerror(self, meeting):
        meeting["duration_minutes"] = None
        with pytest.raises(ValueError, match="duration_minutes"):
            audit_meeting_data(meeting)

    def test_duration_string_raises_valueerror(self, meeting):
        meeting["duration_minutes"] = "60"
        with pytest.raises(ValueError, match="duration_minutes"):
            audit_meeting_data(meeting)

    def test_duration_zero_raises_valueerror(self, meeting):
        meeting["duration_minutes"] = 0
        with pytest.raises(ValueError, match="duration_minutes"):
            audit_meeting_data(meeting)

    def test_duration_negative_raises_valueerror(self, meeting):
        meeting["duration_minutes"] = -30
        with pytest.raises(ValueError, match="duration_minutes"):
            audit_meeting_data(meeting)

    def test_duration_bool_raises_valueerror(self, meeting):
        # bool is a subclass of int in Python; True would otherwise pass int check
        meeting["duration_minutes"] = True
        with pytest.raises(ValueError, match="duration_minutes"):
            audit_meeting_data(meeting)

    # attendees type/shape
    def test_attendees_none_raises_valueerror(self, meeting):
        meeting["attendees"] = None
        with pytest.raises(ValueError, match="attendees"):
            audit_meeting_data(meeting)

    def test_attendees_wrong_type_raises_valueerror(self, meeting):
        meeting["attendees"] = "Alice, Bob"
        with pytest.raises(ValueError, match="attendees"):
            audit_meeting_data(meeting)

    def test_attendees_empty_list_raises_valueerror(self, meeting):
        meeting["attendees"] = []
        with pytest.raises(ValueError, match="attendees"):
            audit_meeting_data(meeting)

    # Optional boolean fields
    @pytest.mark.parametrize("bool_field", ["has_agenda", "has_action_items", "could_be_email"])
    def test_optional_bool_wrong_type_raises_valueerror(self, meeting, bool_field):
        meeting[bool_field] = "yes"
        with pytest.raises(ValueError, match=bool_field):
            audit_meeting_data(meeting)

    # Optional recurrence
    def test_recurrence_unknown_value_raises_valueerror(self, meeting):
        meeting["recurrence"] = "fortnightly"
        with pytest.raises(ValueError, match="recurrence"):
            audit_meeting_data(meeting)

    # Optional fields absent — should use defaults, not raise
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


# ── CLI error handling ────────────────────────────────────────────────────────

class TestCliErrorHandling:
    """Verify that main() surfaces validation errors as readable messages, not tracebacks.

    These tests invoke the CLI as a subprocess so they exercise the real entry
    point, not just the Python API. Validation fires before ensure_cobol_binary()
    is reached, so no COBOL binary is required.
    """

    _ROOT = Path(__file__).parent.parent

    def test_missing_required_fields_clean_error(self, tmp_path):
        bad_json = tmp_path / "bad_meeting.json"
        bad_json.write_text('{"title": "No duration or attendees"}', encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "python/audit_meeting.py", str(bad_json)],
            capture_output=True,
            text=True,
            cwd=self._ROOT,
        )

        assert result.returncode == 1
        assert "Traceback" not in result.stderr
        assert "ERROR" in result.stderr
        assert "duration_minutes" in result.stderr
        assert "attendees" in result.stderr

    def test_invalid_field_type_clean_error(self, tmp_path):
        bad_json = tmp_path / "bad_meeting.json"
        bad_json.write_text(
            '{"title": "Null Attendees", "duration_minutes": 60, "attendees": null}',
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, "python/audit_meeting.py", str(bad_json)],
            capture_output=True,
            text=True,
            cwd=self._ROOT,
        )

        assert result.returncode == 1
        assert "Traceback" not in result.stderr
        assert "ERROR" in result.stderr
        assert "attendees" in result.stderr


# ── Real meeting files ────────────────────────────────────────────────────────

_MEETINGS_DIR = Path(__file__).parent.parent / "meetings"
_MEETING_FILES = sorted(_MEETINGS_DIR.glob("*.json"))
if not _MEETING_FILES:
    raise RuntimeError(f"No meeting JSON files found in {_MEETINGS_DIR}; parametrized tests would silently skip")


class TestRealMeetingFiles:
    """Verify that every committed meeting file passes schema validation.

    Calls _validate_meeting() directly — no COBOL binary required.
    """

    @pytest.mark.parametrize("meeting_path", _MEETING_FILES, ids=[p.stem for p in _MEETING_FILES])
    def test_real_meeting_passes_validation(self, meeting_path):
        with open(meeting_path, encoding="utf-8") as f:
            meeting = json.load(f)
        audit_meeting._validate_meeting(meeting)
