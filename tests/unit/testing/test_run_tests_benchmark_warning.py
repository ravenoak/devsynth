from typing import Any

import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_segmented_run_treats_benchmark_warning_as_success(monkeypatch):
    """
    ReqID: FR-11.2
    When running in segmented mode, if a batch returns a nonzero exit code but
    stderr contains PytestBenchmarkWarning, the batch should be treated as
    successful. This test simulates that path deterministically.
    """

    # Simulate collection returning two node ids
    class DummyCompleted:
        def __init__(self, stdout: str = "", stderr: str = "") -> None:
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = 0

    def fake_run(
        cmd: list[str], check: bool, capture_output: bool, text: bool
    ):  # type: ignore[override]
        # Return minimal collect-only output resembling pytest's -q --collect-only
        # Use python path style entries so _sanitize_node_ids accepts them
        out = "\n".join(
            [
                "tests/unit/sample_test.py::test_one",
                "tests/unit/sample_test.py::test_two",
            ]
        )
        return DummyCompleted(stdout=out, stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    # Simulate pytest execution batches: nonzero returncode
    # but with a benchmark warning in stderr
    class DummyPopen:
        def __init__(
            self,
            cmd: list[str],
            stdout: Any,
            stderr: Any,
            text: bool,
            env: dict[str, str],
        ):  # noqa: D401
            # store for potential assertions/debug
            self.cmd = cmd
            # nonzero return code; handled as success due to warning in stderr
            self._returncode = 1

        def communicate(self):
            stdout = ""
            stderr = "PytestBenchmarkWarning: benchmark plugin present\n"
            return stdout, stderr

        @property
        def returncode(self) -> int:
            return self._returncode

    monkeypatch.setattr("subprocess.Popen", DummyPopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=1,  # force two batches
        parallel=False,
    )

    assert success is True
    assert "PytestBenchmarkWarning" in output
