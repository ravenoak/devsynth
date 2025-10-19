from typing import Any

import pytest

from devsynth.testing import run_tests as rt


class _DummyCompleted:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class _DummyPopen:
    def __init__(self, rc_sequence: list[int]):
        self._rc_seq = rc_sequence
        self._seen: list[list[str]] = []
        self._i = 0

    def __call__(
        self,
        cmd: list[str],
        stdout: Any = None,
        stderr: Any = None,
        text: bool = True,
        env: dict[str, str] | None = None,
    ):
        self._seen.append(cmd)
        idx = self._i
        self._i += 1
        rc = self._rc_seq[idx] if idx < len(self._rc_seq) else 0

        class _Handle:
            def __init__(self, rc: int) -> None:
                self.returncode = rc

            def communicate(self) -> tuple[str, str]:
                # Include a recognizable stderr token to simulate pytest output
                return ("", "ERROR: fail" if rc != 0 else "")

        return _Handle(rc)

    @property
    def seen(self) -> list[list[str]]:
        return self._seen


@pytest.mark.fast
def test_segmented_failure_appends_aggregate_tips_once(monkeypatch, tmp_path):
    """
    ReqID: RT-11 — Aggregated troubleshooting tips appended once after segments.
    """
    # Arrange a fake tests directory and map unit-tests to it
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))

    # Collected node ids => 2 batches with size=2
    collected = [
        "tests/unit/test_a.py::test_1",
        "tests/unit/test_a.py::test_2",
        "tests/unit/test_b.py::test_3",
        "tests/unit/test_b.py::test_4",
    ]

    def fake_run(
        cmd,
        check=False,
        capture_output=False,
        text=False,
        timeout=None,
        cwd=None,
        env=None,
    ):
        if "--collect-only" in cmd:
            return _DummyCompleted(stdout="\n".join(collected), stderr="", returncode=0)
        return _DummyCompleted(stdout="", stderr="", returncode=0)

    # First batch fails (rc=1), second succeeds (rc=0)
    dummy_popen = _DummyPopen(rc_sequence=[1, 0])

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", dummy_popen)

    # Act
    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=2,
        maxfail=1,
        extra_marker=None,
    )

    # Assert: overall not ok due to failed batch
    assert ok is False
    # The troubleshooting tips block should appear once per failed batch (1) plus
    # one aggregated block at the end => total 2 occurrences.
    assert output.count("Troubleshooting tips:") == 2
    # Ensure we spawned two batch runs
    assert len(dummy_popen.seen) == 2
