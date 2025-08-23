"""CLI command to run DevSynth tests.

Wraps :func:`devsynth.testing.run_tests` to provide a `devsynth run-tests`
command. This command mirrors the options exposed by the underlying helper.
Runtime characteristics and termination arguments are documented in
``docs/analysis/run_tests_workflow_analysis.md``.

Example:
    `devsynth run-tests --target unit-tests --speed fast`
"""

from __future__ import annotations

import importlib.util
import os
from typing import Any, Dict, List, Optional

import typer
from typer.models import OptionInfo

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.testing.run_tests import run_tests

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def _parse_feature_options(values: List[str]) -> Dict[str, bool]:
    """Convert ``--feature`` options into a dictionary.

    Each value should be in the form ``name`` or ``name=value`` where ``value``
    can be interpreted as a boolean. If ``value`` is omitted it defaults to
    ``True``.
    """

    if not values or isinstance(values, OptionInfo):
        return {}

    result: Dict[str, bool] = {}
    for item in values:
        if "=" in item:
            name, raw = item.split("=", 1)
            result[name] = raw.lower() not in {"0", "false", "no"}
        else:
            result[item] = True
    return result


OPTIONAL_PROVIDERS = {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "lmstudio"}


def _configure_optional_providers() -> None:
    """Disable tests for missing optional providers.

    Some test suites depend on services like LM Studio. When those services or
    their Python packages aren't available, running the tests can hang while the
    runner waits for an unavailable resource. If the corresponding Python
    package cannot be imported, we default these optional resources to ``false``
    unless explicitly enabled by the user to ensure the corresponding tests are
    skipped rather than stalling the run.
    """

    for env_var, package in OPTIONAL_PROVIDERS.items():
        if env_var in os.environ:
            continue
        if importlib.util.find_spec(package) is None:
            os.environ[env_var] = "false"


def run_tests_cmd(
    target: str = typer.Option(
        "all-tests",
        "--target",
        help="Test target to run",
    ),
    speeds: List[str] = typer.Option(
        [],
        "--speed",
        help="Speed categories to run (can be used multiple times)",
    ),
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
    maxfail: Optional[int] = typer.Option(
        None, "--maxfail", help="Exit after this many failures"
    ),
    features: List[str] = typer.Option(
        [],
        "--feature",
        help="Feature flags to enable/disable (format: name or name=false)",
    ),
    *,
    bridge: Optional[Any] = typer.Option(None, hidden=True),
) -> None:
    """Run DevSynth test suites."""

    ux_bridge = bridge if isinstance(bridge, UXBridge) else globals()["bridge"]

    _configure_optional_providers()

    speed_categories = speeds or None
    feature_map = _parse_feature_options(features)
    if feature_map:
        for name, enabled in feature_map.items():
            env_var = f"DEVSYNTH_FEATURE_{name.upper()}"
            os.environ[env_var] = "true" if enabled else "false"
        logger.info("Feature flags: %s", feature_map)

    success, output = run_tests(
        target,
        speed_categories,
        verbose,
        report,
        not no_parallel,
        segment,
        segment_size,
        maxfail,
    )

    if output:
        ux_bridge.print(output)

    if success:
        ux_bridge.print("[green]Tests completed successfully[/green]")
    else:
        ux_bridge.print("[red]Tests failed[/red]")
        raise typer.Exit(code=1)
