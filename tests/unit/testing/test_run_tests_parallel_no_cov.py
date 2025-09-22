from pathlib import Path

import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_parallel_injects_cov_reports_and_xdist_auto(monkeypatch, tmp_path: Path):
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

    test_a = tmp_path / "test_alpha.py"
    test_b = tmp_path / "test_beta.py"
    test_a.write_text("def test_one():\n    assert True\n")
    test_b.write_text("def test_two():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def fake_run(
        cmd, check=False, capture_output=False, text=False
    ):  # type: ignore[no-untyped-def]
        # Simulate collection with two node ids; pattern
        # ".*\\.py(::|$)" will match them.
        stdout = "\n".join(
            [
                f"{test_a}::test_one",
                f"{test_b}::test_two",
            ]
        )
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

    assert cmd.count("-m") >= 2
    marker_index = len(cmd) - 1 - cmd[::-1].index("-m")
    assert cmd[marker_index + 1] == "fast and not memory_intensive"
