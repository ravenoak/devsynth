"""Validation tests for the `run-tests` CLI options.

ReqID: FR-22, QOL-CLI-Errors
"""

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app


@pytest.mark.fast
def test_invalid_target_exits_with_helpful_message() -> None:
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["run-tests", "--target", "weird-tests"])  # nosec

    assert result.exit_code == 2
    assert "Invalid --target value" in result.output
    assert "all-tests|unit-tests|integration-tests|behavior-tests" in result.output


@pytest.mark.fast
def test_invalid_speed_exits_with_helpful_message() -> None:
    runner = CliRunner()
    app = build_app()
    # Include one valid and one invalid to ensure detection
    result = runner.invoke(
        app,
        [
            "run-tests",
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--speed",
            "warp",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid --speed value(s)" in result.output
    assert "fast|medium|slow" in result.output
