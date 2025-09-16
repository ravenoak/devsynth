"""Tests for ``scripts/verify_coverage_threshold.py``. ReqID: Task-21.9"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import verify_coverage_threshold as vct


def _write_coverage_file(path: Path, percent: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"totals": {"percent_covered": percent}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.fast
def test_verify_coverage_threshold_passes_when_above(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI succeeds when coverage meets the threshold. ReqID: Task-21.9"""
    coverage_file = _write_coverage_file(tmp_path / "coverage.json", 95.5)

    exit_code = vct.main(["--coverage-file", str(coverage_file)])

    captured = capsys.readouterr()
    assert exit_code == vct.EXIT_SUCCESS
    assert "meets the" in captured.out


@pytest.mark.fast
def test_verify_coverage_threshold_fails_when_below(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI fails when coverage drops below the threshold. ReqID: Task-21.9"""
    coverage_file = _write_coverage_file(tmp_path / "coverage.json", 82.3)

    exit_code = vct.main(["--coverage-file", str(coverage_file), "--threshold", "90"])

    captured = capsys.readouterr()
    assert exit_code == vct.EXIT_BELOW_THRESHOLD
    assert "below the required" in captured.err
