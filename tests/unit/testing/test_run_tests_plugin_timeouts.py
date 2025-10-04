from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

pytest_plugins = ["tests.unit.testing"]

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_collect_tests_with_cache_handles_subprocess_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Timeouts during collection surface a warning and yield no tests."""

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", tmp_path / ".cache")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "sample_test.py").write_text("def test_sample():\n    assert True\n")

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=["pytest"], timeout=rt.DEFAULT_COLLECTION_TIMEOUT_SECONDS
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    with caplog.at_level(logging.WARNING, logger="devsynth.testing.run_tests"):
        collected = rt.collect_tests_with_cache("unit-tests")

    assert collected == []
    assert "Test collection failed" in caplog.text
    assert "pytest" in caplog.text


@pytest.mark.fast
def test_collect_tests_with_cache_honors_env_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit timeout override is forwarded to the subprocess call."""

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", tmp_path / ".cache")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "sample_test.py").write_text("def test_sample():\n    assert True\n")

    monkeypatch.setenv("DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS", "42")

    captured_kwargs: dict[str, object] = {}

    def fake_run(*_args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured_kwargs.update(kwargs)
        return subprocess.CompletedProcess(
            args=["pytest"],
            returncode=0,
            stdout="tests/sample_test.py::test_sample\n",
            stderr="",
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    collected = rt.collect_tests_with_cache("unit-tests")

    assert collected == ["tests/sample_test.py::test_sample"]
    assert float(captured_kwargs["timeout"]) == pytest.approx(42.0)
