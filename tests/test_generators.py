"""
Tests for scheduled-generator error handling.

Each generator must:
  - Skip malformed JSON files with a WARNING to stderr (no traceback)
  - Skip files that fail schema validation with a WARNING (no traceback)
  - Still produce a report when at least one valid meeting exists
  - Exit 0 when at least one valid meeting was processed
"""

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_MEETINGS_DIR = _ROOT / "meetings"

_GENERATORS = [
    "python/generate_daily_digest.py",
    "python/generate_preflight.py",
    "python/generate_weekly_entropy.py",
]


def _run_generator(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        cwd=_ROOT,
        timeout=60,
    )


@pytest.fixture()
def bad_meeting_file(tmp_path):
    """Write a malformed JSON file into meetings/, yield its path, then remove it."""
    bad = _MEETINGS_DIR / "_test_malformed_fixture.json"
    bad.write_text("{not valid json", encoding="utf-8")
    yield bad
    bad.unlink(missing_ok=True)


@pytest.mark.parametrize("script", _GENERATORS)
def test_malformed_json_is_skipped_not_fatal(bad_meeting_file, script):
    """Generator exits 0 and emits WARNING for the bad file, no Traceback."""
    result = _run_generator(script)

    assert result.returncode == 0, (
        f"{script} exited {result.returncode}\nstderr:\n{result.stderr}"
    )
    assert "WARNING" in result.stderr, (
        f"Expected WARNING in stderr for bad file\nstderr:\n{result.stderr}"
    )
    assert bad_meeting_file.name in result.stderr, (
        f"Expected bad filename in stderr\nstderr:\n{result.stderr}"
    )
    assert "Traceback" not in result.stderr, (
        f"Unexpected traceback in stderr\nstderr:\n{result.stderr}"
    )


@pytest.mark.parametrize("script", _GENERATORS)
def test_malformed_json_warning_names_file(bad_meeting_file, script):
    """The WARNING line contains the exact filename of the bad file."""
    result = _run_generator(script)
    warning_lines = [l for l in result.stderr.splitlines() if "WARNING" in l]
    assert any(bad_meeting_file.name in l for l in warning_lines), (
        f"No WARNING line contains '{bad_meeting_file.name}'\nstderr:\n{result.stderr}"
    )
