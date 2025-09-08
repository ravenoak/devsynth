import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_keyword_filter_lmstudio_no_matches_returns_success(monkeypatch):
    """ReqID: TR-RT-08 — Keyword 'lmstudio' no-match returns success.

    When extra_marker includes requires_resource('lmstudio') and collection
    yields no matching node ids, run_tests should return success=True with a
    helpful message without attempting to execute pytest on any node ids.
    """

    class DummyRunResult:
        def __init__(self):
            self.stdout = ""  # no node ids collected
            self.stderr = ""
            self.returncode = 0

    calls = {
        "run": [],
        "popen": [],
    }

    def fake_run(
        cmd, check=False, capture_output=True, text=True
    ):  # type: ignore[override]
        calls["run"].append(cmd)
        return DummyRunResult()

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # type: ignore[no-redef]
            calls["popen"].append(cmd)
            # This path should not be reached because no node ids => early return
            self._stdout = ""
            self._stderr = ""
            self.returncode = 0

        def communicate(self):
            return self._stdout, self._stderr

    import subprocess

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(subprocess, "Popen", FakePopen)

    success, output = run_tests(
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

    assert success is True
    assert "No tests matched" in output
    # Ensure collection was attempted with collect-only and keyword filter
    # (-k lmstudio)
    assert any(
        "--collect-only" in cmd for cmd in calls["run"]
    )  # type: ignore[arg-type]
    # Verify that the command contains -k lmstudio
    assert any(
        ("-k" in cmd) and ("lmstudio" in cmd) for cmd in calls["run"]
    )  # type: ignore[arg-type]
    # Ensure Popen was never invoked due to early return
    assert calls["popen"] == []


@pytest.mark.fast
def test_extra_marker_merges_into_m_expression(monkeypatch):
    """ReqID: TR-RT-09 — Non-keyword extra_marker merges into -m expression."""
    """
    When extra_marker does not invoke the keyword fallback, ensure it is merged
    into the -m expression and subprocess.Popen is called once; run_tests returns
    success if the process returncode is 0.
    """

    class FakePopen:
        last_cmd = None

        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # type: ignore[no-redef]
            FakePopen.last_cmd = cmd
            self.returncode = 0
            self._stdout = "pytest ok\n"
            self._stderr = ""

        def communicate(self):
            return self._stdout, self._stderr

    import subprocess

    def fake_run(
        cmd, check=False, capture_output=True, text=True
    ):  # type: ignore[override]
        # Not used in this path; ensure it's not called unnecessarily
        raise AssertionError("subprocess.run should not be called for non-keyword path")

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    monkeypatch.setattr(subprocess, "run", fake_run)

    extra = "slow or (requires_resource('codebase'))"
    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker=extra,
    )

    assert success is True
    assert "pytest ok" in output
    # The constructed command should include "-m" and the merged marker expression
    assert "-m" in FakePopen.last_cmd
    # Expression should contain the base not memory_intensive marker
    assert any(arg.find("not memory_intensive") != -1 for arg in FakePopen.last_cmd)
    # and also include our extra marker text
    assert any(
        arg.find("requires_resource('codebase')") != -1 for arg in FakePopen.last_cmd
    )
