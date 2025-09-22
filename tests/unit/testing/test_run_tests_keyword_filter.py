from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_keyword_filter_no_matches_returns_success_message(tmp_path, monkeypatch):
    """ReqID: FR-11.2 — Keyword filter path returns success when no matches.

    Triggers the lmstudio keyword path and expects a friendly message.
    """
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def fake_collect(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        assert "--collect-only" in cmd
        assert "-k" in cmd and "lmstudio" in cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)

    # Use a very specific marker expression to trigger keyword path.
    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        extra_marker="requires_resource('lmstudio')",
    )
    assert success is True
    assert "No tests matched" in output


@pytest.mark.fast
def test_keyword_filter_honors_report_flag_and_creates_report_dir(
    monkeypatch, tmp_path
):
    """ReqID: FR-11.2 — Report flag creates deterministic report directory.

    Use keyword path with report=True and patch datetime to assert directory path.
    """
    class FakeDT:
        @staticmethod
        def now():
            # Fixed timestamp for stable directory path
            class _DT:
                def strftime(self, fmt: str) -> str:
                    return "20250101_000000"

            return _DT()

    monkeypatch.setattr(rt, "datetime", FakeDT)

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    test_file = tmp_path / "test_lmstudio.py"
    test_file.write_text("def test_placeholder():\n    assert True\n")

    def fake_collect(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        assert "--collect-only" in cmd
        assert "-k" in cmd and "lmstudio" in cmd
        return SimpleNamespace(
            returncode=0,
            stdout=f"{test_file}::test_placeholder",
            stderr="",
        )

    class FakePopen:
        def __init__(self, cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001
            self.cmd = list(cmd)
            self.returncode = 0
            self._stdout = "ok"
            self._stderr = ""

        def communicate(self):  # noqa: D401 - mimic subprocess API
            """Return deterministic stdout/stderr."""

            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=True,
        parallel=False,
        segment=False,
        extra_marker='requires_resource("lmstudio")',
    )
    assert success is True
    # Report path is logged; ensure directory exists
    expected_dir = Path("test_reports/20250101_000000/unit-tests")
    assert expected_dir.exists()
