"""CLI command to run DevSynth tests.

Wraps :func:`devsynth.testing.run_tests` to provide a `devsynth run-tests`
command. This command mirrors the options exposed by the underlying helper.

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
from devsynth.observability.metrics import increment_counter

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


from devsynth.config.provider_env import ProviderEnv

OPTIONAL_PROVIDERS = {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "lmstudio"}


def _configure_optional_providers() -> None:
    """Disable or gate optional/remote providers by default in test runs.

    This function sets conservative defaults so that running tests (especially
    fast/smoke paths) never block on unavailable external resources. It uses a
    typed ProviderEnv to ensure consistent parsing and defaults across the codebase.
    """

    # Always default optional resources to disabled for test runs unless the user explicitly opted in.
    if "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" not in os.environ:
        os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "false"

    # Apply offline-first, stub-by-default provider settings for tests
    env = ProviderEnv.from_env().with_test_defaults()
    env.apply_to_env()


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
    smoke: bool = typer.Option(
        False,
        "--smoke",
        help="Run in smoke mode: disable xdist and third-party pytest plugins for stability",
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
    """Run DevSynth test suites.

    For workflow and performance details see
    ``docs/analysis/run_tests_workflow.md``.
    """

    ux_bridge = bridge if isinstance(bridge, UXBridge) else globals()["bridge"]

    _configure_optional_providers()

    # Record a lightweight invocation metric (no-op if prometheus not installed)
    try:
        increment_counter(
            "devsynth_cli_run_tests_invocations",
            {"target": target, "smoke": str(smoke).lower()},
            description="Count of devsynth run-tests CLI invocations",
        )
    except Exception:
        # Never let observability failures interfere with CLI behavior
        pass

    # Validate options early with actionable messages.
    allowed_targets = {"all-tests", "unit-tests", "integration-tests", "behavior-tests"}
    if target not in allowed_targets:
        ux_bridge.print(
            "[red]Invalid --target value:[/red] '" + target + "'. "
            "Allowed: all-tests|unit-tests|integration-tests|behavior-tests. "
            "See docs/user_guides/cli_reference.md for details."
        )
        raise typer.Exit(code=2)

    normalized_speeds = [s.lower() for s in (speeds or [])]
    allowed_speeds = {"fast", "medium", "slow"}
    invalid_speeds = [s for s in normalized_speeds if s not in allowed_speeds]
    if invalid_speeds:
        ux_bridge.print(
            "[red]Invalid --speed value(s):[/red] " + ", ".join(invalid_speeds) + ". "
            "Allowed: fast|medium|slow. Use multiple --speed flags to combine."
        )
        raise typer.Exit(code=2)

    # Smoke mode: minimize plugin surface and disable xdist
    if smoke:
        os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        # Explicitly disable xdist plugin if present
        os.environ.setdefault("PYTEST_ADDOPTS", "-p no:xdist -p no:cov")
        no_parallel = True
        # In smoke mode, default to fast tests when no explicit speeds are provided.
        if not normalized_speeds:
            normalized_speeds = ["fast"]
        # Enforce a conservative per-test timeout for smoke runs unless overridden
        os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "5")

    # For explicit fast-only runs (and not smoke), apply a slightly looser timeout
    # to catch stalls while avoiding flakiness on slower machines.
    if not smoke:
        if normalized_speeds and set(normalized_speeds) == {"fast"}:
            os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "10")

    speed_categories = normalized_speeds or None
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
