from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_segment_batch_failure_appends_tips(monkeypatch) -> None:
    """ReqID: RT-08 — segmented batch failure appends troubleshooting tips and fails."""

    collected_ids = (
        "tests/unit/mod_x_test.py::test_x1\n" "tests/unit/mod_y_test.py::test_y1\n"
    )

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        assert "--collect-only" in cmd and "-q" in cmd
        return SimpleNamespace(returncode=0, stdout=collected_ids, stderr="")

    class FailingBatch:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            self._stderr = "boom"  # no benchmark warning
            self.returncode = 1

        def communicate(self) -> tuple[str, str]:
            return ("", self._stderr)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", FailingBatch)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker=None,
    )

    assert success is False
    assert "Pytest exited with code" in output
    assert "Troubleshooting tips:" in output


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_segment_batch_benchmark_warning_forces_success(monkeypatch) -> None:
    """ReqID: RT-09 — PytestBenchmarkWarning in stderr forces success for the batch."""

    collected_ids = (
        "tests/unit/mod_x_test.py::test_x1\n" "tests/unit/mod_y_test.py::test_y1\n"
    )

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        return SimpleNamespace(returncode=0, stdout=collected_ids, stderr="")

    class WarnBatch:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            self._stderr = "PytestBenchmarkWarning: calibration"
            self.returncode = 1  # would fail without the special-case handling

        def communicate(self) -> tuple[str, str]:
            return ("ok\n", self._stderr)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", WarnBatch)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    assert "PytestBenchmarkWarning" in output
