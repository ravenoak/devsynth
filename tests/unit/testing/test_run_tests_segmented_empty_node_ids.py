import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_tests_segmented_falls_back_on_empty_collection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: RUN-TESTS-SEGMENTED-5 — Fallback run executes when no node ids exist."""

    tests_dir = tmp_path / "segmented-empty"
    tests_dir.mkdir()
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda _env: False)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda _env: False)

    def fake_collect(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)

    popen_calls: list[list[str]] = []

    class FakePopen:
        def __init__(
            self,
            cmd,
            stdout=None,
            stderr=None,
            text=True,
            env=None,
        ):  # noqa: ANN001
            popen_calls.append(cmd[:])
            self.returncode = 0
            self._stdout = "ok\n"
            self._stderr = ""

        def communicate(self):  # noqa: D401 - simple stub
            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    caplog.set_level(logging.WARNING)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=10,
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    assert "Segmented execution requested" in caplog.text
    assert len(popen_calls) == 1
    run_command = popen_calls[0]
    assert run_command[-3:] == [
        str(tests_dir),
        "-m",
        "fast and not memory_intensive",
    ]
    assert "ok" in output
