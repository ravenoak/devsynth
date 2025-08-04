"""CLI command to run DevSynth tests.

Wraps :func:`devsynth.testing.run_tests` to provide a `devsynth run-tests`
command. This command mirrors the options exposed by the underlying helper.

Example:
    `devsynth run-tests --target unit-tests --fast`
"""

from __future__ import annotations

from typing import Optional

import typer

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.testing.run_tests import run_tests

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def run_tests_cmd(
    target: str = typer.Option(
        "all-tests",
        "--target",
        help="Test target to run",
    ),
    fast: bool = typer.Option(False, "--fast", help="Run only fast tests"),
    medium: bool = typer.Option(False, "--medium", help="Run only medium tests"),
    slow: bool = typer.Option(False, "--slow", help="Run only slow tests"),
    report: bool = typer.Option(False, "--report", help="Generate HTML report"),
    verbose: bool = typer.Option(False, "--verbose", help="Show verbose output"),
    no_parallel: bool = typer.Option(
        False, "--no-parallel", help="Disable parallel test execution"
    ),
    segment: bool = typer.Option(
        False, "--segment", help="Run tests in smaller batches"
    ),
    segment_size: int = typer.Option(
        50, "--segment-size", help="Number of tests per batch when segmenting"
    ),
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Run DevSynth test suites."""

    ux_bridge = bridge or globals()["bridge"]

    speed_categories = []
    if fast:
        speed_categories.append("fast")
    if medium:
        speed_categories.append("medium")
    if slow:
        speed_categories.append("slow")
    if not speed_categories:
        speed_categories = None

    success, _ = run_tests(
        target,
        speed_categories,
        verbose,
        report,
        not no_parallel,
        segment,
        segment_size,
    )

    if success:
        ux_bridge.print("[green]Tests completed successfully[/green]")
    else:
        ux_bridge.print("[red]Tests failed[/red]")
        raise typer.Exit(code=1)
