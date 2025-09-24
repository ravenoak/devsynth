"""Unit tests for :func:`devsynth.testing.run_tests.coverage_artifacts_status`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_coverage_status_reports_missing_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing JSON should return ``False`` with a helpful reason."""

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", tmp_path / "cov.json")
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", tmp_path / "htmlcov")

    ok, reason = rt.coverage_artifacts_status()
    assert ok is False
    assert str(tmp_path / "cov.json") in (reason or "")


@pytest.mark.fast
def test_coverage_status_flags_invalid_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Malformed JSON surfaces a descriptive message."""

    json_path = tmp_path / "coverage.json"
    json_path.write_text("{not-json}")
    html_dir = tmp_path / "htmlcov"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<!doctype html><title>coverage</title>")

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)

    ok, reason = rt.coverage_artifacts_status()
    assert ok is False
    assert "invalid" in (reason or "").lower()


@pytest.mark.fast
def test_coverage_status_requires_totals(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """JSON without ``totals.percent_covered`` is rejected."""

    json_path = tmp_path / "coverage.json"
    json_path.write_text(json.dumps({"meta": {}}))
    html_dir = tmp_path / "htmlcov"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<!doctype html><title>coverage</title>")

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)

    ok, reason = rt.coverage_artifacts_status()
    assert ok is False
    assert "totals" in (reason or "")


@pytest.mark.fast
def test_coverage_status_requires_html_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing HTML index is surfaced."""

    json_path = tmp_path / "coverage.json"
    json_path.write_text(json.dumps({"totals": {"percent_covered": 91.0}}))

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", tmp_path / "htmlcov")

    ok, reason = rt.coverage_artifacts_status()
    assert ok is False
    assert "html" in (reason or "").lower()


@pytest.mark.fast
def test_coverage_status_rejects_empty_html(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """HTML indicating no coverage data should fail the status check."""

    json_path = tmp_path / "coverage.json"
    json_path.write_text(json.dumps({"totals": {"percent_covered": 93.0}}))
    html_dir = tmp_path / "htmlcov"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("No coverage data available")

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)

    ok, reason = rt.coverage_artifacts_status()
    assert ok is False
    assert "no recorded data" in (reason or "").lower()


@pytest.mark.fast
def test_coverage_status_success_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Valid JSON and HTML return ``True`` and ``None``."""

    json_path = tmp_path / "coverage.json"
    json_path.write_text(json.dumps({"totals": {"percent_covered": 97.5}}))
    html_dir = tmp_path / "htmlcov"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<!doctype html><p>Coverage OK</p>")

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)

    ok, reason = rt.coverage_artifacts_status()
    assert ok is True
    assert reason is None
