from pathlib import Path

import pytest

import devsynth.testing.run_tests as rt


class DummyCompleted:
    def __init__(self, stdout: str, stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class DummyPopen:
    def __init__(
        self, returncode: int = 0, stdout: str = "ok", stderr: str = ""
    ) -> None:
        self._returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    def communicate(self):
        return self._stdout, self._stderr

    @property
    def returncode(self) -> int:  # type: ignore[override]
        return self._returncode


@pytest.mark.fast
def test_keyword_marker_executes_matching_node_ids(monkeypatch, tmp_path: Path) -> None:
    """ReqID: TR-RT-07 — Keyword-based exec path runs collected node ids."""
    # Prepare collection output with two node ids
    collect_stdout = "\n".join(
        [
            "tests/unit/test_sample.py::test_a",
            "tests/unit/test_sample.py::test_b",
        ]
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
        # Simulate the '--collect-only' run
        return DummyCompleted(stdout=collect_stdout, returncode=0)

    def fake_popen(cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001
        # Ensure that the selected node ids appear in the run command
        assert any("test_sample.py::test_a" in s for s in cmd), cmd
        assert any("test_sample.py::test_b" in s for s in cmd), cmd
        return DummyPopen(returncode=0, stdout="passed", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker="requires_resource('lmstudio')",
    )
    assert ok is True
    assert "passed" in output or output == ""
