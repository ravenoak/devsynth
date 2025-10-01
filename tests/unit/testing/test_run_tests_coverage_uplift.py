from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture
def coverage_artifact_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> SimpleNamespace:
    """Configure run_tests coverage paths within a temporary directory."""
    monkeypatch.chdir(tmp_path)
    coverage_json_path = tmp_path / "reports" / "coverage.json"
    html_dir = tmp_path / "reports" / "html"
    legacy_dir = tmp_path / "legacy" / "html"
    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", coverage_json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(rt, "LEGACY_HTML_DIRS", (legacy_dir,))
    return SimpleNamespace(
        coverage_json=coverage_json_path,
        html_dir=html_dir,
        legacy_dir=legacy_dir,
        data_file=tmp_path / ".coverage",
    )


@pytest.mark.fast
def test_failure_tips_formats_return_code_and_cmd(caplog: pytest.LogCaptureFixture):
    """Asserts _failure_tips formats the command and return code correctly."""
    returncode = 127
    cmd = ["poetry", "run", "pytest", "-k", "nonexistent"]
    tips = rt._failure_tips(returncode, cmd)
    assert f"Pytest exited with code {returncode}" in tips
    assert f"Command: {' '.join(cmd)}" in tips


@pytest.mark.fast
def test_reset_coverage_artifacts_handles_oserror(
    coverage_artifact_environment: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    """Asserts _reset_coverage_artifacts logs but does not raise on OSError."""
    env = coverage_artifact_environment
    env.data_file.touch()

    # Mock unlink to raise an error to test the exception handling
    mock_unlink = MagicMock(side_effect=OSError("Permission denied"))
    monkeypatch.setattr(Path, "unlink", mock_unlink)

    caplog.set_level(logging.DEBUG)

    rt._reset_coverage_artifacts()

    assert "Unable to remove coverage artifact" in caplog.text
    # Ensure it was called for the file we created
    mock_unlink.assert_any_call()


@pytest.mark.fast
def test_ensure_coverage_artifacts_handles_unreadable_html(
    coverage_artifact_environment: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
):
    """Asserts a warning is returned if the HTML report is unreadable."""
    env = coverage_artifact_environment
    env.coverage_json.parent.mkdir(parents=True, exist_ok=True)
    env.coverage_json.write_text(json.dumps({"totals": {"percent_covered": 90.0}}))
    html_index = env.html_dir / "index.html"
    html_index.parent.mkdir(parents=True, exist_ok=True)
    html_index.touch()

    original_read_text = Path.read_text

    def fake_read_text(self, *args, **kwargs):
        if self == html_index:
            raise OSError("Test read error")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    ok, reason = rt.coverage_artifacts_status()

    assert not ok
    assert reason is not None
    assert "Coverage HTML unreadable" in reason
