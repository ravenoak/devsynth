import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_parallel_injects_cov_reports_and_xdist_auto(monkeypatch):
    """ReqID: TR-RT-11 — Parallel path injects -n auto with coverage reports.

    Verify that when parallel=True, run_tests injects xdist flags and preserves
    coverage instrumentation so JSON/HTML artifacts are generated.
    """

    called = {}

    class FakeCompleted:
        def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    def fake_run(
        cmd, check=False, capture_output=False, text=False
    ):  # type: ignore[no-untyped-def]
        # Simulate collection with two node ids; pattern
        # ".*\\.py(::|$)" will match them.
        stdout = "foo_test.py::test_one\n" "bar_test.py::test_two\n"
        return FakeCompleted(stdout=stdout, stderr="", returncode=0)

    # pragma: no cover - communicate() path is asserted via effects
    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # type: ignore[no-untyped-def]
            called["cmd"] = cmd
            self.returncode = 0

        def communicate(self):  # type: ignore[no-untyped-def]
            return ("", "")

    # Patch subprocess in module under test
    monkeypatch.setattr("devsynth.testing.run_tests.subprocess.run", fake_run)
    monkeypatch.setattr("devsynth.testing.run_tests.subprocess.Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=True,
        segment=False,
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    assert "ERRORS:" not in output

    cmd = called.get("cmd")
    assert isinstance(cmd, list), f"expected list command, got: {type(cmd)}"

    # Assert xdist auto and coverage disabled flags are present
    assert "-n" in cmd and "auto" in cmd, f"xdist flags not present in cmd: {cmd}"
    cov_flag = f"--cov={rt.COVERAGE_TARGET}"
    json_flag = f"--cov-report=json:{rt.COVERAGE_JSON_PATH}"
    html_flag = f"--cov-report=html:{rt.COVERAGE_HTML_DIR}"
    assert cov_flag in cmd, f"{cov_flag} not present in cmd: {cmd}"
    assert json_flag in cmd, f"{json_flag} not present in cmd: {cmd}"
    assert html_flag in cmd, f"{html_flag} not present in cmd: {cmd}"
    assert "--cov-append" in cmd, f"--cov-append not present in cmd: {cmd}"

    # Node ids from collection should be passed through to the run command
    assert any(isinstance(x, str) and x.endswith("foo_test.py::test_one") for x in cmd)
    assert any(isinstance(x, str) and x.endswith("bar_test.py::test_two") for x in cmd)
