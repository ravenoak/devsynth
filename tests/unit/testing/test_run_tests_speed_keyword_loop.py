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
def test_speed_loop_uses_keyword_filter_and_executes_node_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: TR-RT-08 — Speed-loop applies keyword filter and executes IDs.

    Simulate collection inside the speed loop with '-m <expr>' and
    '-k lmstudio'.
    """
    test_root = tmp_path
    file_path = test_root / "test_kwfast.py"
    file_path.write_text("def test_1():\n    assert True\n\ndef test_2():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(test_root))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(test_root))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    collect_stdout = "\n".join(
        [
            f"{file_path}::test_1",
            f"{file_path}::test_2",
        ]
    )

    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        # Ensure '-k lmstudio' applied during collection in speed loop
        assert "-k" in cmd and "lmstudio" in cmd, cmd
        return DummyCompleted(stdout=collect_stdout, returncode=0)

    def fake_popen(cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001
        # Ensure that both node ids are passed to execution command
        joined = " ".join(cmd)
        assert "test_kwfast.py::test_1" in joined, cmd
        assert "test_kwfast.py::test_2" in joined, cmd
        return DummyPopen(returncode=0, stdout="passed", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=50,
        maxfail=None,
        extra_marker="requires_resource('lmstudio')",
    )
    assert ok is True
    assert "passed" in output or output == ""
