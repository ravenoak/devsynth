"""Focused tests for coverage artifact management and ``run_tests`` flow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as run_tests_module

from .run_tests_test_utils import build_batch_metadata


@pytest.fixture
def coverage_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Point coverage artifact constants at a temporary workspace."""

    coverage_json = tmp_path / "test_reports" / "coverage.json"
    html_dir = tmp_path / "htmlcov"
    monkeypatch.setattr(run_tests_module, "COVERAGE_JSON_PATH", coverage_json)
    monkeypatch.setattr(run_tests_module, "COVERAGE_HTML_DIR", html_dir)
    return coverage_json, html_dir


@pytest.mark.fast
def test_reset_coverage_artifacts_removes_stale_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Existing coverage outputs should be deleted prior to a new run."""

    monkeypatch.chdir(tmp_path)
    coverage_json = tmp_path / "test_reports" / "coverage.json"
    html_dir = tmp_path / "htmlcov"
    legacy_dir = tmp_path / "test_reports" / "htmlcov"

    monkeypatch.setattr(run_tests_module, "COVERAGE_JSON_PATH", coverage_json)
    monkeypatch.setattr(run_tests_module, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(run_tests_module, "LEGACY_HTML_DIRS", (legacy_dir,))

    (tmp_path / ".coverage").write_text("data")
    (tmp_path / "coverage.json").write_text("legacy")
    (tmp_path / ".coverage.machine").write_text("fragment")
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<html></html>")
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "index.html").write_text("legacy html")

    run_tests_module._reset_coverage_artifacts()

    assert not (tmp_path / ".coverage").exists()
    assert not (tmp_path / "coverage.json").exists()
    assert not list(tmp_path.glob(".coverage.*"))
    assert not html_dir.exists()
    assert not legacy_dir.exists()


@pytest.mark.fast
def test_ensure_coverage_artifacts_generates_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fragmented coverage data should consolidate into HTML and JSON reports."""

    monkeypatch.chdir(tmp_path)
    coverage_json = tmp_path / "test_reports" / "coverage.json"
    html_dir = tmp_path / "htmlcov"
    legacy_dir = tmp_path / "test_reports" / "htmlcov"

    monkeypatch.setattr(run_tests_module, "COVERAGE_JSON_PATH", coverage_json)
    monkeypatch.setattr(run_tests_module, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(run_tests_module, "LEGACY_HTML_DIRS", (legacy_dir,))

    fragment_one = tmp_path / ".coverage.001"
    fragment_two = tmp_path / ".coverage.002"
    fragment_one.write_text("one")
    fragment_two.write_text("two")

    class DummyCoverage:
        def __init__(self, data_file: str) -> None:
            self.data_file = Path(data_file)

        def combine(self, paths: list[str]) -> None:
            self.data_file.write_text("combined")

        def save(self) -> None:
            self.data_file.write_text("combined")

        def load(self) -> None:  # pragma: no cover - simple stub
            pass

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(measured_files=lambda: {"src/devsynth/module.py"})

        def html_report(self, directory: str) -> None:
            html_path = Path(directory)
            html_path.mkdir(parents=True, exist_ok=True)
            (html_path / "index.html").write_text("<html>covered</html>")

        def json_report(self, outfile: str) -> None:
            Path(outfile).write_text(json.dumps({"totals": {"percent_covered": 99.0}}))

    monkeypatch.setitem(
        sys.modules, "coverage", SimpleNamespace(Coverage=DummyCoverage)
    )

    run_tests_module._ensure_coverage_artifacts()

    consolidated = tmp_path / ".coverage"
    assert consolidated.exists()
    assert (
        json.loads((tmp_path / "coverage.json").read_text())["totals"][
            "percent_covered"
        ]
        == 99.0
    )
    assert (html_dir / "index.html").exists()
    assert (legacy_dir / "index.html").exists()
    assert not fragment_one.exists()
    assert not fragment_two.exists()


@pytest.mark.fast
def test_run_tests_fails_when_pytest_cov_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing pytest-cov plugin should surface a coverage remediation message."""

    monkeypatch.setattr(run_tests_module, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(
        run_tests_module, "ensure_pytest_cov_plugin_env", lambda env: None
    )
    monkeypatch.setattr(
        run_tests_module, "ensure_pytest_bdd_plugin_env", lambda env: None
    )
    monkeypatch.setattr(
        run_tests_module,
        "pytest_cov_support_status",
        lambda env: (False, run_tests_module.PYTEST_COV_PLUGIN_MISSING_MESSAGE),
    )

    with pytest.raises(run_tests_module.PytestCovMissingError) as excinfo:
        run_tests_module.run_tests("unit-tests", ["fast"], env={})

    assert run_tests_module.PYTEST_COV_PLUGIN_MISSING_MESSAGE in str(excinfo.value)


@pytest.mark.fast
def test_run_tests_successful_single_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful execution should include runner output and publication notice."""

    monkeypatch.setattr(run_tests_module, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(
        run_tests_module, "ensure_pytest_cov_plugin_env", lambda env: None
    )
    monkeypatch.setattr(
        run_tests_module, "ensure_pytest_bdd_plugin_env", lambda env: None
    )
    monkeypatch.setattr(
        run_tests_module, "pytest_cov_support_status", lambda env: (True, None)
    )

    def fake_collect(
        target: str, speed: str | None, *, keyword_filter: str | None = None
    ) -> list[str]:
        return [f"{target}::{speed or 'all'}::test_case"]

    monkeypatch.setattr(run_tests_module, "collect_tests_with_cache", fake_collect)

    def fake_single_batch(
        config: run_tests_module.SingleBatchRequest,
    ) -> run_tests_module.BatchExecutionResult:
        assert list(config.node_ids)
        return (
            True,
            "pytest ok",
            build_batch_metadata("batch-artifacts", command=["pytest"], returncode=0),
        )

    monkeypatch.setattr(run_tests_module, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(run_tests_module, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(
        run_tests_module,
        "_maybe_publish_coverage_evidence",
        lambda **__: "[knowledge-graph] coverage ingested",
    )

    success, output = run_tests_module.run_tests(
        "unit-tests",
        ["fast"],
        report=True,
        env={},
    )

    assert success is True
    assert "pytest ok" in output
    assert "coverage ingested" in output


@pytest.mark.fast
def test_coverage_artifacts_status_handles_missing_json(
    coverage_paths: tuple[Path, Path],
) -> None:
    """Missing JSON artifacts should surface a descriptive remediation message."""

    coverage_json, html_dir = coverage_paths
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "index.html").write_text("<html>empty</html>")

    ok, reason = run_tests_module.coverage_artifacts_status()
    assert ok is False
    assert reason is not None and str(coverage_json) in reason


@pytest.mark.fast
def test_coverage_artifacts_status_rejects_invalid_json(
    coverage_paths: tuple[Path, Path],
) -> None:
    """Invalid coverage JSON payloads should be rejected with context."""

    coverage_json, html_dir = coverage_paths
    coverage_json.parent.mkdir(parents=True, exist_ok=True)
    coverage_json.write_text("not-json")
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "index.html").write_text("<html>ok</html>")

    ok, reason = run_tests_module.coverage_artifacts_status()
    assert ok is False
    assert reason is not None and "invalid" in reason


@pytest.mark.fast
def test_coverage_artifacts_status_detects_missing_html(
    coverage_paths: tuple[Path, Path],
) -> None:
    """When the HTML report is absent the helper should flag the gap."""

    coverage_json, _ = coverage_paths
    coverage_json.parent.mkdir(parents=True, exist_ok=True)
    coverage_json.write_text(json.dumps({"totals": {"percent_covered": 91.2}}))

    ok, reason = run_tests_module.coverage_artifacts_status()
    assert ok is False
    assert reason is not None and "Coverage HTML missing" in reason


@pytest.mark.fast
def test_coverage_artifacts_status_detects_empty_html(
    coverage_paths: tuple[Path, Path],
) -> None:
    """HTML reports that note missing data should trigger remediation."""

    coverage_json, html_dir = coverage_paths
    coverage_json.parent.mkdir(parents=True, exist_ok=True)
    coverage_json.write_text(json.dumps({"totals": {"percent_covered": 90.0}}))
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "index.html").write_text("No coverage data available")

    ok, reason = run_tests_module.coverage_artifacts_status()
    assert ok is False
    assert reason is not None and "No coverage data" in reason


@pytest.mark.fast
def test_coverage_artifacts_status_success(coverage_paths: tuple[Path, Path]) -> None:
    """Valid coverage artifacts should return a positive status."""

    coverage_json, html_dir = coverage_paths
    coverage_json.parent.mkdir(parents=True, exist_ok=True)
    coverage_json.write_text(json.dumps({"totals": {"percent_covered": 93.5}}))
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "index.html").write_text("<html>coverage ok</html>")

    ok, reason = run_tests_module.coverage_artifacts_status()
    assert ok is True
    assert reason is None


@pytest.mark.fast
def test_failure_tips_includes_command_context() -> None:
    """Failure tips prefix the command and retain segmentation guidance."""

    cmd = ["python", "-m", "pytest", "tests/unit"]
    tips = run_tests_module._failure_tips(2, cmd)

    assert tips.startswith(
        "\nPytest exited with code 2. Command: python -m pytest tests/unit"
    )
    assert "Troubleshooting tips:" in tips
    assert "Segment large suites" in tips
    assert "Re-run failing segments" in tips
