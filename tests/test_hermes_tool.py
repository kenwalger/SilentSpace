"""
Tests for python/hermes_meeting_tool.py — Hermes agent tool boundary.

All tests invoke the tool as a subprocess. This exercises the real entry point,
argument parsing, error handling, and exit codes without requiring in-process
imports of the tool module.

Runtime dependency: tests that invoke audit_meeting_data() via the tool require
the COBOL binary (same dependency as the main test suite). Tests for invalid
JSON and missing fields exit before reaching the binary.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_TOOL = "python/hermes_meeting_tool.py"

_VALID_MEETING = {
    "title": "Hermes Tool Test Meeting",
    "recurrence": "none",
    "duration_minutes": 30,
    "attendees": ["Alice", "Bob"],
    "has_agenda": True,
    "has_action_items": True,
    "could_be_email": False,
    "organizer": "alice@test.com",
    "description": "A meeting that exists solely to satisfy the test suite.",
}


def _run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    """Run hermes_meeting_tool.py with the given arguments."""
    cmd = [sys.executable, _TOOL] + list(args)
    return subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=_ROOT,
    )


# ── File input ─────────────────────────────────────────────────────────────────

class TestFileInput:
    def test_valid_meeting_file_exits_zero(self):
        result = _run("meetings/weekly_alignment_sync.json")
        assert result.returncode == 0, result.stderr

    def test_valid_meeting_file_stdout_is_json(self):
        result = _run("meetings/weekly_alignment_sync.json")
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)

    def test_output_has_required_keys(self):
        result = _run("meetings/weekly_alignment_sync.json")
        parsed = json.loads(result.stdout)
        for key in ("title", "waste_score", "necessity_prob", "classification", "recommendation", "meeting"):
            assert key in parsed, f"Missing key: {key!r}"

    def test_waste_score_is_int_in_range(self):
        result = _run("meetings/weekly_alignment_sync.json")
        parsed = json.loads(result.stdout)
        assert isinstance(parsed["waste_score"], int)
        assert 0 <= parsed["waste_score"] <= 100

    def test_necessity_prob_is_int_in_range(self):
        result = _run("meetings/weekly_alignment_sync.json")
        parsed = json.loads(result.stdout)
        assert isinstance(parsed["necessity_prob"], int)
        assert 5 <= parsed["necessity_prob"] <= 100

    def test_title_matches_input(self):
        result = _run("meetings/weekly_alignment_sync.json")
        parsed = json.loads(result.stdout)
        assert parsed["title"] == "Weekly Alignment Sync"

    def test_nothing_on_stderr_for_valid_input(self):
        result = _run("meetings/weekly_alignment_sync.json")
        assert result.returncode == 0
        assert result.stderr == ""


# ── Stdin input ────────────────────────────────────────────────────────────────

class TestStdinInput:
    def test_valid_meeting_stdin_exits_zero(self):
        result = _run("--stdin", stdin=json.dumps(_VALID_MEETING))
        assert result.returncode == 0, result.stderr

    def test_valid_meeting_stdin_stdout_is_json(self):
        result = _run("--stdin", stdin=json.dumps(_VALID_MEETING))
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)

    def test_stdin_output_has_required_keys(self):
        result = _run("--stdin", stdin=json.dumps(_VALID_MEETING))
        parsed = json.loads(result.stdout)
        for key in ("title", "waste_score", "necessity_prob", "classification", "recommendation", "meeting"):
            assert key in parsed

    def test_stdin_title_matches_input(self):
        result = _run("--stdin", stdin=json.dumps(_VALID_MEETING))
        parsed = json.loads(result.stdout)
        assert parsed["title"] == _VALID_MEETING["title"]


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_no_args_exits_nonzero(self):
        result = _run()
        assert result.returncode != 0

    def test_no_args_prints_to_stderr(self):
        result = _run()
        assert result.stderr != "" or result.returncode != 0

    def test_both_file_and_stdin_exits_nonzero(self, tmp_path):
        f = tmp_path / "m.json"
        f.write_text(json.dumps(_VALID_MEETING), encoding="utf-8")
        result = _run(str(f), "--stdin", stdin=json.dumps(_VALID_MEETING))
        assert result.returncode != 0

    def test_file_not_found_exits_1(self):
        result = _run("meetings/no_such_meeting.json")
        assert result.returncode == 1

    def test_file_not_found_prints_error(self):
        result = _run("meetings/no_such_meeting.json")
        assert "ERROR" in result.stderr

    def test_invalid_json_in_file_exits_2(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json}", encoding="utf-8")
        result = _run(str(bad))
        assert result.returncode == 2

    def test_invalid_json_in_file_prints_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json}", encoding="utf-8")
        result = _run(str(bad))
        assert "ERROR" in result.stderr
        assert "JSON" in result.stderr

    def test_invalid_json_on_stdin_exits_2(self):
        result = _run("--stdin", stdin="{not valid json}")
        assert result.returncode == 2

    def test_invalid_json_on_stdin_prints_error(self):
        result = _run("--stdin", stdin="{not valid json}")
        assert "ERROR" in result.stderr


# ── Missing required fields ────────────────────────────────────────────────────

class TestMissingFields:
    def _write_json(self, tmp_path, data: dict) -> str:
        f = tmp_path / "m.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        return str(f)

    def test_missing_title_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        del m["title"]
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_missing_title_mentions_field(self, tmp_path):
        m = dict(_VALID_MEETING)
        del m["title"]
        result = _run(self._write_json(tmp_path, m))
        assert "title" in result.stderr

    def test_missing_duration_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        del m["duration_minutes"]
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_missing_attendees_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        del m["attendees"]
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_empty_dict_exits_3(self, tmp_path):
        result = _run(self._write_json(tmp_path, {}))
        assert result.returncode == 3

    def test_empty_dict_error_lists_all_required(self, tmp_path):
        result = _run(self._write_json(tmp_path, {}))
        for field in ("title", "duration_minutes", "attendees"):
            assert field in result.stderr


# ── Invalid field types ────────────────────────────────────────────────────────

class TestInvalidFieldTypes:
    def _write_json(self, tmp_path, data: dict) -> str:
        f = tmp_path / "m.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        return str(f)

    def test_title_int_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        m["title"] = 42
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_duration_string_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        m["duration_minutes"] = "60"
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_attendees_null_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        m["attendees"] = None
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_attendees_string_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        m["attendees"] = "Alice, Bob"
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    @pytest.mark.parametrize("field", ["has_agenda", "has_action_items", "could_be_email"])
    def test_bool_field_string_exits_3(self, tmp_path, field):
        m = dict(_VALID_MEETING)
        m[field] = "yes"
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3

    def test_unknown_recurrence_exits_3(self, tmp_path):
        m = dict(_VALID_MEETING)
        m["recurrence"] = "fortnightly"
        result = _run(self._write_json(tmp_path, m))
        assert result.returncode == 3


# ── --write-report ─────────────────────────────────────────────────────────────

class TestWriteReport:
    def test_write_report_exits_zero(self):
        result = _run(
            "meetings/weekly_alignment_sync.json",
            "--write-report",
        )
        assert result.returncode == 0, result.stderr

    def test_write_report_output_includes_report_path(self):
        result = _run(
            "meetings/weekly_alignment_sync.json",
            "--write-report",
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "report_path" in parsed

    def test_write_report_file_exists(self):
        result = _run(
            "meetings/weekly_alignment_sync.json",
            "--write-report",
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        report_path = Path(parsed["report_path"])
        assert report_path.exists(), f"Report file not found: {report_path}"
