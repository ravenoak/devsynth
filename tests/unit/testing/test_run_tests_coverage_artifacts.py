import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
@pytest.mark.test_metrics
def test_coverage_artifacts_created_when_no_tests(tmp_path, monkeypatch):
    """ReqID: run-tests-coverage-no-tests"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setitem(rt.TARGET_PATHS, "dummy-tests", str(empty_dir))
    monkeypatch.setattr(
        rt.subprocess,
        "run",
        lambda *args, **kwargs: type(
            "R",
            (),
            {"stdout": "", "stderr": "", "returncode": 5},
        )(),
    )

    class DummyPopen:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            self.returncode = 5

        def communicate(self):  # noqa: ANN001
            return "", ""

    monkeypatch.setattr(rt.subprocess, "Popen", DummyPopen)
    monkeypatch.chdir(tmp_path)
    success, _ = rt.run_tests("dummy-tests", ["fast"], report=False, parallel=False)
    assert success
    html_index = tmp_path / "htmlcov" / "index.html"
    assert html_index.exists()
    assert html_index.read_text().strip() != ""
    assert (tmp_path / "test_reports" / "coverage.json").exists()


@pytest.mark.fast
@pytest.mark.test_metrics
def test_coverage_artifacts_created_for_aggregated_speeds(tmp_path, monkeypatch):
    """Aggregated fast+medium runs should emit coverage artifacts."""

    monkeypatch.chdir(tmp_path)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    sample_test = tests_dir / "test_sample.py"
    sample_test.write_text("def test_sample():\n    assert True\n")

    monkeypatch.setattr(
        rt,
        "TARGET_PATHS",
        {"dummy-tests": "tests", "all-tests": "tests"},
    )

    node_output = "test_sample.py::test_sample\n"

    def fake_collect(
        cmd, check=False, capture_output=False, text=False
    ):  # type: ignore[no-untyped-def]
        assert "--collect-only" in cmd
        return type(
            "R",
            (),
            {"stdout": node_output, "stderr": "", "returncode": 0},
        )()

    commands: list[list[str]] = []

    class DummyProcess:
        def __init__(self, cmd, stdout=None, stderr=None, text=False, env=None):  # type: ignore[no-untyped-def]
            commands.append(cmd)
            self.returncode = 0

        def communicate(self):  # type: ignore[no-untyped-def]
            return ("ok", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", DummyProcess)

    success, _ = rt.run_tests(
        "dummy-tests",
        ["fast", "medium"],
        report=False,
        parallel=False,
    )

    assert success is True
    assert commands, "Expected coverage-enabled pytest invocations"
    for cmd in commands:
        assert f"--cov={rt.COVERAGE_TARGET}" in cmd
        assert f"--cov-report=json:{rt.COVERAGE_JSON_PATH}" in cmd
        assert f"--cov-report=html:{rt.COVERAGE_HTML_DIR}" in cmd
        assert "--cov-append" in cmd

    html_index = tmp_path / "htmlcov" / "index.html"
    assert html_index.exists()
    assert html_index.read_text().strip() != ""

    cov_json = tmp_path / "test_reports" / "coverage.json"
    assert cov_json.exists()
    assert cov_json.read_text().strip() != ""
