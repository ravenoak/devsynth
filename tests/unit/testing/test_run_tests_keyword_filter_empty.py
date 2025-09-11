import sys

import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_run_tests_lmstudio_keyword_filter_with_no_matches_returns_success(monkeypatch):
    """
    ReqID: C3-05
    When extra_marker requires_resource('lmstudio') is provided and the keyword-filtered
    collection yields no tests, run_tests should short-circuit and return success=True
    with a friendly message instead of attempting to invoke pytest with empty args.
    """

    # Simulate `pytest --collect-only -q -m <expr> -k lmstudio` returning no node IDs.
    class DummyCompleted:
        def __init__(self, stdout: str = "", returncode: int = 0):
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_run(
        cmd: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
    ):  # type: ignore[no-redef]
        # Ensure we're calling a python -m pytest command with '--collect-only'
        assert cmd[:3] == [sys.executable, "-m", "pytest"], cmd
        assert "--collect-only" in cmd
        # Return empty stdout to indicate no matched tests
        return DummyCompleted(stdout="", returncode=0)

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")  # keep hermetic and fast
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")

    monkeypatch.setattr("subprocess.run", fake_run)

    # Call run_tests with an lmstudio resource marker expression
    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,  # triggers the single-pass branch
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
