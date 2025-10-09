"""Additional targeted tests for :mod:`devsynth.testing.run_tests`."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt

pytestmark = pytest.mark.fast


def test_failure_tips_mentions_core_troubleshooting_flags() -> None:
    """Tips include smoke, segment, maxfail, no-parallel, and report guidance.

    ReqID: coverage-run-tests
    """

    tips = rt._failure_tips(1, ["python", "-m", "pytest"])
    for expected in ["--smoke", "--segment", "--maxfail", "--no-parallel", "--report"]:
        assert expected in tips


def test_ensure_pytest_cov_plugin_env_injects_and_skips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plugin flag is appended only when coverage remains enabled.

    ReqID: coverage-run-tests
    """

    env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    assert rt.ensure_pytest_cov_plugin_env(env) is True
    assert env["PYTEST_ADDOPTS"].endswith("-p pytest_cov")

    env_no_cov = {
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTEST_ADDOPTS": "--no-cov",
    }
    assert rt.ensure_pytest_cov_plugin_env(env_no_cov) is False


def test_coverage_artifacts_status_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Valid coverage JSON and HTML return success.

    ReqID: coverage-run-tests
    """

    json_path = tmp_path / "coverage.json"
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<html>covered</html>")
    json_path.write_text(json.dumps({"totals": {"percent_covered": 91.2}}))

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", json_path)
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)

    ok, reason = rt.coverage_artifacts_status()
    assert ok is True
    assert reason is None


def test_coverage_artifacts_status_missing_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing coverage JSON surfaces a detailed error message.

    ReqID: coverage-run-tests
    """

    html_dir = tmp_path / "html"
    html_dir.mkdir()
    (html_dir / "index.html").write_text("<html>covered</html>")

    monkeypatch.setattr(rt, "COVERAGE_JSON_PATH", tmp_path / "coverage.json")
    monkeypatch.setattr(rt, "COVERAGE_HTML_DIR", html_dir)

    ok, reason = rt.coverage_artifacts_status()
    assert ok is False
    assert "Coverage JSON missing" in reason


def test_enforce_coverage_threshold_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Threshold enforcement returns the parsed percentage on success.

    ReqID: coverage-run-tests
    """

    payload = {"totals": {"percent_covered": 95.5}}
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(payload))

    percent = rt.enforce_coverage_threshold(
        report_path, minimum_percent=90.0, exit_on_failure=False
    )
    assert percent == pytest.approx(95.5)


def test_enforce_coverage_threshold_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing data and low percentages raise runtime errors when exit is disabled.

    ReqID: coverage-run-tests
    """

    missing_path = tmp_path / "missing.json"
    with pytest.raises(RuntimeError):
        rt.enforce_coverage_threshold(missing_path, exit_on_failure=False)

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("not-json")
    with pytest.raises(RuntimeError):
        rt.enforce_coverage_threshold(invalid_path, exit_on_failure=False)

    no_totals = tmp_path / "no_totals.json"
    no_totals.write_text(json.dumps({}))
    with pytest.raises(RuntimeError):
        rt.enforce_coverage_threshold(no_totals, exit_on_failure=False)

    low_path = tmp_path / "low.json"
    low_path.write_text(json.dumps({"totals": {"percent_covered": 10}}))
    with pytest.raises(RuntimeError):
        rt.enforce_coverage_threshold(
            low_path, minimum_percent=50, exit_on_failure=False
        )


def test_sanitize_node_ids_removes_line_numbers() -> None:
    """Collection node IDs lose redundant trailing line numbers without duplicates.

    ReqID: coverage-run-tests
    """

    raw = [
        "tests/unit/test_example.py:42",
        "tests/unit/test_example.py:42",
        "tests/unit/test_example.py::TestSuite::test_case",
    ]
    sanitized = rt._sanitize_node_ids(raw)
    assert sanitized == [
        "tests/unit/test_example.py",
        "tests/unit/test_example.py::TestSuite::test_case",
    ]


def test_collect_tests_with_cache_handles_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Timeouts during collection yield tips but no crash.

    ReqID: coverage-run-tests
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "1")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", "tests")
    (tmp_path / "tests").mkdir()

    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        return SimpleNamespace(stdout="", stderr="", returncode=-1)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    collected = rt.collect_tests_with_cache("unit-tests", speed_category="fast")
    assert collected == []
