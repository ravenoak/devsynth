"""Segmentation regression tests for :mod:`devsynth.testing.run_tests`.

Issue: issues/coverage-below-threshold.md — exercise batching, plugin fallbacks,
coverage gating warnings, and remediation guidance surfaced by ``run_tests``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_segmented_batches_surface_plugin_fallbacks_and_failure_tips(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RUN-TESTS-SEGMENTATION-1 — Segmented failures emit rich diagnostics.

    This test simulates a segmented execution where the first batch fails with a
    coverage gate error. It verifies that fallback plugin injection occurs for the
    subprocess environment, coverage warnings propagate to stdout/stderr, and the
    aggregated failure guidance from :func:`_failure_tips` is appended exactly once.
    """

    caplog.set_level(logging.INFO)

    tests_dir = tmp_path / "segmented"
    tests_dir.mkdir()
    test_one = tests_dir / "test_one.py"
    test_two = tests_dir / "test_two.py"
    test_one.write_text("def test_one():\n    assert True\n")
    test_two.write_text("def test_two():\n    assert True\n")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path / "cache"))

    # Avoid mutating real coverage artifacts while exercising segmentation logic.
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    coverage_calls: list[str] = []
    monkeypatch.setattr(
        rt, "_ensure_coverage_artifacts", lambda: coverage_calls.append("ensured")
    )

    ensure_calls: list[tuple[str, bool, str]] = []

    def fake_cov(env: dict[str, str]) -> bool:
        ensure_calls.append(("cov", env is os.environ, env.get("PYTEST_ADDOPTS", "")))
        if env is os.environ:
            # Simulate a no-op at the process level so the subprocess copy applies the fix.
            return False
        env["PYTEST_ADDOPTS"] = (
            env.get("PYTEST_ADDOPTS", "") + " -p pytest_cov"
        ).strip()
        return True

    def fake_bdd(env: dict[str, str]) -> bool:
        ensure_calls.append(("bdd", env is os.environ, env.get("PYTEST_ADDOPTS", "")))
        if env is os.environ:
            return False
        env["PYTEST_ADDOPTS"] = (
            env.get("PYTEST_ADDOPTS", "") + " -p pytest_bdd.plugin"
        ).strip()
        return True

    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", fake_cov)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", fake_bdd)

    collect_output = "\n".join(
        [
            f"{test_one}::test_one",
            f"{test_two}::test_two",
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
        assert "--collect-only" in cmd, "collection command expected"
        return SimpleNamespace(returncode=0, stdout=collect_output, stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    batch_plan = iter(
        [
            {
                "returncode": 1,
                "stdout": "batch-one\n",
                "stderr": "FAIL Required test coverage of 90% not reached.\n",
            },
            {
                "returncode": 0,
                "stdout": "batch-two\n",
                "stderr": "",
            },
        ]
    )
    popen_calls: list[dict[str, object]] = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            popen_calls.append({"cmd": list(cmd), "env": dict(env or {})})
            try:
                result = next(batch_plan)
            except StopIteration as exc:  # pragma: no cover - guards test integrity
                raise AssertionError("Unexpected extra Popen invocation") from exc
            self.returncode = result["returncode"]
            self._stdout = result["stdout"]
            self._stderr = result["stderr"]

        def communicate(self):  # noqa: D401 - signature mirrors subprocess API
            """Return the stubbed stdout/stderr pair."""

            return self._stdout, self._stderr

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
        extra_marker=None,
    )

    # Segmented run should detect the coverage gate failure and report tips twice
    # (once for the failing batch, once for the aggregated remediation block).
    assert success is False
    assert "FAIL Required test coverage of 90% not reached." in output
    assert output.count("Pytest exited with code 1") == 2
    assert output.count("Troubleshooting tips:") == 2
    # Coverage lifecycle still runs even though the batch failed.
    assert coverage_calls == ["ensured"]

    # Plugin fallbacks were attempted both for the process env and the subprocess copy.
    assert ("cov", True, "") in ensure_calls
    assert ("bdd", True, "") in ensure_calls
    assert any(
        name == "cov" and is_os_env is False for name, is_os_env, _ in ensure_calls
    )
    assert any(
        name == "bdd" and is_os_env is False and "pytest_cov" in addopts
        for name, is_os_env, addopts in ensure_calls
    )

    assert len(popen_calls) == 2
    first_env = popen_calls[0]["env"]
    assert "-p pytest_cov" in first_env.get("PYTEST_ADDOPTS", "")
    assert "-p pytest_bdd.plugin" in first_env.get("PYTEST_ADDOPTS", "")

    # The failing batch stderr is surfaced to the log output for operator awareness.
    assert "FAIL Required test coverage of 90% not reached." in caplog.text
