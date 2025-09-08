"""Inner test mode behavior tests for run-tests CLI.

Covers the DEVSYNTH_INNER_TEST branch which reduces plugin surface and forces
no-parallel, ensuring predictable, fast inner subprocess validations.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module


@pytest.mark.fast
def test_inner_test_mode_disables_plugins_and_parallel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: FR-11.2 — Inner test mode disables plugins and parallel.

    Verifies DEVSYNTH_INNER_TEST=1 forces PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and
    injects -p no:xdist -p no:cov, and passes parallel=False to run_tests.
    """
    # Ensure a clean environment for the test
    monkeypatch.setenv("DEVSYNTH_INNER_TEST", "1")
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    # Prepare CLI runner and patch run_tests to avoid executing pytest
    runner = CliRunner()
    with patch.object(module, "run_tests", return_value=(True, "")) as mock_run:
        app = build_app()
        # Use explicit target/speed to avoid any other branches changing defaults
        result = runner.invoke(
            app,
            [
                "run-tests",
                "--target",
                "unit-tests",
                "--speed",
                "fast",
            ],
        )

    # CLI should succeed
    assert result.exit_code == 0, result.output

    # Environment should have been set to disable third-party plugins and coverage
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    assert "-p no:xdist" in addopts
    assert "-p no:cov" in addopts

    # run_tests should have been invoked with parallel=False due to no_parallel=True
    # Signature:
    # run_tests(target, speed_categories, verbose, report,
    #           parallel, segment, segment_size, maxfail, **kwargs)
    assert mock_run.called, "run_tests was not invoked"
    args, kwargs = mock_run.call_args
    # 5th positional arg (index 4) is 'parallel'
    assert args[4] is False, f"Expected parallel=False, got {args[4]!r}"
