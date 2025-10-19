from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_collect_tests_with_cache_handles_subprocess_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RT-ERR-01 — Collection errors log tips and return empty list.

    Issue: issues/coverage-below-threshold.md
    """

    tests_dir = tmp_path / "tests_root"
    tests_dir.mkdir()
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    caplog.set_level(logging.ERROR)

    def boom(*_args, **_kwargs):  # noqa: ANN002
        raise RuntimeError("collection failed")

    monkeypatch.setattr(rt.subprocess, "run", boom)

    result = rt.collect_tests_with_cache("unit-tests", speed_category="fast")

    assert result == []
    assert "collection failed" in caplog.text
    assert "Pytest exited" in caplog.text


@pytest.mark.fast
def test_run_tests_handles_unexpected_execution_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RT-ERR-02 — Unexpected execution errors surface troubleshooting tips.

    Issue: issues/coverage-below-threshold.md
    """

    tests_dir = tmp_path / "tests_exec"
    tests_dir.mkdir()
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)

    def failing_popen(*_args, **_kwargs):  # noqa: ANN002
        raise RuntimeError("boom popen")

    monkeypatch.setattr(rt.subprocess, "Popen", failing_popen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker=None,
    )

    assert success is False
    assert "boom popen" in output
    assert "Troubleshooting tips" in output


@pytest.mark.fast
def test_run_tests_segment_merges_extra_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RT-ERR-03 — Segmented runs combine marker filters with extra expressions.

    Issue: issues/coverage-below-threshold.md
    """

    tests_dir = tmp_path / "tests_segment"
    tests_dir.mkdir()
    (tests_dir / "test_demo.py").write_text("def test_ok():\n    assert True\n")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))

    node_ids = "test_demo.py::test_ok\n"

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        assert "--collect-only" in cmd
        marker_index = len(cmd) - 1 - cmd[::-1].index("-m")
        expr = cmd[marker_index + 1]
        assert "fast" in expr and "not memory_intensive" in expr
        assert "not slow" in expr
        return SimpleNamespace(returncode=0, stdout=node_ids, stderr="")

    captured_batches: list[list[str]] = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            captured_batches.append(cmd)
            self.returncode = 0

        def communicate(self):
            return ("ok\n", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker="not slow",
    )

    assert success is True
    assert any("test_demo.py::test_ok" in " ".join(cmd) for cmd in captured_batches)
    assert "ok" in output or output == ""
