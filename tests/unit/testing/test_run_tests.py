from __future__ import annotations

import os
from typing import Any

import pytest

import devsynth.testing.run_tests as rt


class DummyProc:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    def communicate(self) -> tuple[str, str]:
        return self._stdout, self._stderr


@pytest.fixture(autouse=True)
def clear_cache(monkeypatch: pytest.MonkeyPatch):
    # prevent env bleed
    monkeypatch.delenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", raising=False)
    yield


@pytest.mark.fast
@pytest.mark.isolation
def test_parallel_and_maxfail_and_report_builds_cmd(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """ReqID: RT-01 — run_tests composes args for parallel, maxfail, report, and speed filters."""
    calls: dict[str, Any] = {"run": [], "popen": []}

    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001, ARG002
        calls["run"].append(cmd)
        # Simulate collect-only returning two node IDs
        out = "\n".join(["tests/unit/test_a.py::t1", "tests/unit/test_b.py::t2"]) + "\n"
        class R:
            def __init__(self):
                self.returncode = 0
                self.stdout = out
                self.stderr = ""
        return R()

    def fake_popen(cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001, ARG002
        calls["popen"].append(cmd)
        return DummyProc(0, stdout="ok\n", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=True,
        parallel=True,
        segment=False,
        segment_size=2,
        maxfail=1,
    )

    assert success is True
    assert "ok" in output
    # Popen called once with combined node ids, includes -n auto and --no-cov
    popen_cmd = calls["popen"][0]
    assert "-n" in popen_cmd and "auto" in popen_cmd
    assert "--no-cov" in popen_cmd
    # Maxfail should be present in both collect and run commands
    all_cmd_text = " ".join(" ".join(c) for c in (calls["run"][0], popen_cmd))
    assert "--maxfail=1" in all_cmd_text
    # Report options should include pytest-html flags
    assert any("--html=" in tok for tok in popen_cmd)


@pytest.mark.fast
@pytest.mark.isolation
def test_segment_batches(monkeypatch: pytest.MonkeyPatch):
    """ReqID: RT-02 — segmentation runs in batches respecting segment_size."""
    calls: list[list[str]] = []

    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001, ARG002
        # simulate 5 node ids
        out = "\n".join([f"tests/unit/test_a.py::t{i}" for i in range(5)]) + "\n"
        class R:
            def __init__(self):
                self.returncode = 0
                self.stdout = out
                self.stderr = ""
        return R()

    def fake_popen(cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001, ARG002
        calls.append(cmd)
        return DummyProc(0, stdout="batch\n", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, out = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=2,
        report=False,
        parallel=False,
    )

    assert success is True
    # Expect 3 batches for 5 tests with size 2
    assert len(calls) == 3


@pytest.mark.fast
@pytest.mark.isolation
def test_failure_tips_appended(monkeypatch: pytest.MonkeyPatch):
    """ReqID: RT-03 — non-zero return adds troubleshooting tips and success False."""
    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001, ARG002
        out = "tests/unit/test_a.py::t1\n"
        class R:
            def __init__(self):
                self.returncode = 0
                self.stdout = out
                self.stderr = ""
        return R()

    def fake_popen(cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001, ARG002
        return DummyProc(2, stdout="", stderr="boom")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, out = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        report=False,
        parallel=False,
    )

    assert success is False
    assert "Troubleshooting tips:" in out


@pytest.mark.fast
@pytest.mark.isolation
def test_collect_cache_determinism(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """ReqID: RT-04 — collect_tests_with_cache uses cache on second call."""
    # point cache dir into tmp to avoid project writes
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path))
    calls = {"run": 0}

    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001, ARG002
        calls["run"] += 1
        out = "tests/unit/test_x.py::t1\n"
        class R:
            def __init__(self):
                self.returncode = 0
                self.stdout = out
                self.stderr = ""
        return R()

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    lst1 = rt.collect_tests_with_cache("unit-tests", "fast")
    lst2 = rt.collect_tests_with_cache("unit-tests", "fast")

    assert lst1 == lst2
    # Only first call should have invoked subprocess.run thanks to cache
    assert calls["run"] == 1
