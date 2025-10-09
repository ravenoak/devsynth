"""Tests for ``scripts/find_syntax_errors.py``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.fast]


def run_script(path: Path) -> subprocess.CompletedProcess[str]:
    """Run the script against ``path`` and return the completed process."""

    script = Path(__file__).resolve().parents[3] / "scripts" / "find_syntax_errors.py"
    return subprocess.run(
        [sys.executable, str(script), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_returns_error_when_syntax_is_invalid(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

    result = run_script(tmp_path)

    assert result.returncode == 1
    assert "SyntaxError" in result.stdout


def test_returns_zero_with_no_errors(tmp_path: Path) -> None:
    good_file = tmp_path / "good.py"
    good_file.write_text("print('ok')\n", encoding="utf-8")

    result = run_script(tmp_path)

    assert result.returncode == 0
    assert "No syntax errors found" in result.stdout
