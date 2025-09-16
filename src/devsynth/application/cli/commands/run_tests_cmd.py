"""CLI command to run DevSynth tests.

Wraps :func:`devsynth.testing.run_tests` to provide a `devsynth run-tests`
command. This command mirrors the options exposed by the underlying helper.

Example:
    `devsynth run-tests --target unit-tests --speed fast`
"""

from __future__ import annotations

import os
from typing import Any

import typer

from devsynth.config.provider_env import ProviderEnv
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.observability.metrics import increment_counter
from devsynth.testing.run_tests import (
    COVERAGE_HTML_DIR,
    COVERAGE_JSON_PATH,
    DEFAULT_COVERAGE_THRESHOLD,
    collect_tests_with_cache,
    enforce_coverage_threshold,
    run_tests,
)

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def _parse_feature_options(values: list[str]) -> dict[str, bool]:
    """Convert ``--feature`` options into a dictionary.

    Each value should be in the form ``name`` or ``name=value`` where ``value``
    can be interpreted as a boolean. If ``value`` is omitted it defaults to
    ``True``.
    """

    # Typer always passes a list for multi-option flags; guard defensively
    # for runtime safety.
    if not values:
        return {}

    result: dict[str, bool] = {}
    for item in values:
        if "=" in item:
            name, raw = item.split("=", 1)
            result[name] = raw.lower() not in {"0", "false", "no"}
        else:
            result[item] = True
    return result


OPTIONAL_PROVIDERS = {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "lmstudio"}


def _configure_optional_providers() -> None:
    """Disable or gate optional/remote providers by default in test runs.

    This function sets conservative defaults so that running tests (especially
    fast/smoke paths) never block on unavailable external resources. It uses a
    typed ProviderEnv to ensure consistent parsing and defaults across the codebase.
    """

    # Always default optional resources to disabled for test runs unless the
    # user explicitly opted in.
    if "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" not in os.environ:
        os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "false"

    # Apply offline-first, stub-by-default provider settings for tests
    env = ProviderEnv.from_env().with_test_defaults()
    env.apply_to_env()


def _emit_coverage_artifact_messages(ux_bridge: UXBridge) -> None:
    """Provide operator feedback about generated coverage artifacts."""

    html_index = COVERAGE_HTML_DIR / "index.html"
    if html_index.exists() and html_index.stat().st_size > 0:
        ux_bridge.print(
            "[green]HTML coverage report available at[/green] "
            + str(html_index.resolve())
        )
    else:
        ux_bridge.print(
            "[yellow]HTML coverage report missing or empty at[/yellow] "
            + str(html_index.resolve())
        )

    if COVERAGE_JSON_PATH.exists() and COVERAGE_JSON_PATH.stat().st_size > 0:
        ux_bridge.print(
            "[green]Coverage JSON written to[/green] "
            + str(COVERAGE_JSON_PATH.resolve())
        )
    else:
        ux_bridge.print(
            "[yellow]Coverage JSON missing or empty at[/yellow] "
            + str(COVERAGE_JSON_PATH.resolve())
        )


def run_tests_cmd(
    target: str = typer.Option(
        "all-tests",
        "--target",
        help="Test target to run",
    ),
    speeds: list[str] = typer.Option(
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
        help=(
            "Run in smoke mode: disable xdist and third-party pytest plugins "
            "for stability"
        ),
    ),
    segment: bool = typer.Option(
        False, "--segment", help="Run tests in smaller batches"
    ),
    segment_size: int = typer.Option(
        50, "--segment-size", help="Number of tests per batch when segmenting"
    ),
    maxfail: int | None = typer.Option(
        None, "--maxfail", help="Exit after this many failures"
    ),
    features: list[str] = typer.Option(
        [],
        "--feature",
        help="Feature flags to enable/disable (format: name or name=false)",
    ),
    inventory: bool = typer.Option(
        False,
        "--inventory",
        help="Export test inventory to test_reports/test_inventory.json and exit",
    ),
    marker: str | None = typer.Option(
        None,
        "-m",
        "--marker",
        help=(
            "Additional pytest marker expression to AND with speed filters "
            "(e.g., requires_resource('lmstudio'))"
        ),
    ),
    *,
    bridge: str | None = typer.Option(None, hidden=True),
) -> None:
    """Run DevSynth test suites.

    For workflow and performance details see
    ``docs/analysis/run_tests_workflow.md``.
    """

    ux_bridge = bridge if isinstance(bridge, UXBridge) else globals()["bridge"]

    # When invoked programmatically (not via Typer CLI), parameters defined with
    # typer.Option(...) can be passed as Typer Option objects rather than their
    # concrete types. Normalize such values for predictable behavior in tests.
    # Normalize values in case this is called programmatically (not via Typer CLI)
    if not isinstance(inventory, bool):
        # Treat unspecified inventory flag as False when called directly.
        inventory = False

    if not isinstance(speeds, list):  # Typer OptionInfo or None
        speeds = []

    if not isinstance(features, list):  # Typer OptionInfo or None
        features = []

    _configure_optional_providers()

    # Allow 'responses' library to intercept requests cleanly in unit tests.
    # We keep low-level sockets blocked in tests/fixtures/networking.py, so
    # real network egress is still prevented. This only relaxes the guard
    # that patches requests.request/Session.request, which interferes with
    # responses in some environments.
    if (
        os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS") is None
        and os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1"
        and target == "unit-tests"
    ):
        # Apply by default for unit-tests target; other targets can opt-in via env.
        # This preserves hermeticity while enabling standard mocking patterns.
        os.environ["DEVSYNTH_TEST_ALLOW_REQUESTS"] = "true"

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
            "[red]Invalid --target value:[/red] '"
            + str(target)
            + "'. Allowed: all-tests|unit-tests|integration-tests|behavior-tests. "
            + "See docs/user_guides/cli_command_reference.md for details."
        )
        raise typer.Exit(code=2)

    normalized_speeds = [s.lower() for s in (speeds or [])]
    allowed_speeds = {"fast", "medium", "slow"}
    invalid_speeds = [s for s in normalized_speeds if s not in allowed_speeds]
    if invalid_speeds:
        ux_bridge.print(
            "[red]Invalid --speed value(s):[/red] "
            + ", ".join(invalid_speeds)
            + ". Allowed: fast|medium|slow. Use multiple --speed flags to combine."
        )
        raise typer.Exit(code=2)

    # Inventory-only mode: export JSON and exit successfully without running tests
    if inventory:
        import json as _json
        from datetime import datetime as _dt
        from pathlib import Path as _Path

        targets = ["all-tests", "unit-tests", "integration-tests", "behavior-tests"]
        speeds_all = ["fast", "medium", "slow"]
        inventory_data: dict[str, dict[str, list[str]]] = {}
        for tgt in targets:
            inventory_data[tgt] = {}
            for spd in speeds_all:
                try:
                    inventory_data[tgt][spd] = collect_tests_with_cache(tgt, spd)
                except Exception:
                    inventory_data[tgt][spd] = []
        report_dir = _Path("test_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        out_path = report_dir / "test_inventory.json"
        payload = {
            "generated_at": _dt.utcnow().isoformat() + "Z",
            "targets": inventory_data,
        }
        out_path.write_text(_json.dumps(payload, indent=2))
        ux_bridge.print("[green]Test inventory exported to[/green] " + str(out_path))
        return

    # Smoke mode: minimize plugin surface and disable xdist
    if smoke:
        os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        # Explicitly disable xdist plugin if present
        os.environ.setdefault("PYTEST_ADDOPTS", "-p no:xdist")
        no_parallel = True
        # In smoke mode, default to fast tests when no explicit speeds are provided.
        if not normalized_speeds:
            normalized_speeds = ["fast"]
        # Enforce a conservative per-test timeout for smoke runs unless overridden
        os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "30")

    # Optimize inner subprocess validation runs used by tests: disable plugins
    # and parallelism to avoid timeouts and reduce startup overhead, but only
    # when explicitly indicated by tests.
    if os.environ.get("DEVSYNTH_INNER_TEST") == "1":
        os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        existing_addopts = os.environ.get("PYTEST_ADDOPTS", "")
        # Prepend to ensure our flags take effect
        os.environ["PYTEST_ADDOPTS"] = (
            "-p no:xdist " + existing_addopts
        ).strip()
        no_parallel = True

    # For explicit fast-only runs (and not smoke), apply a slightly looser timeout
    # to catch stalls while avoiding flakiness on slower machines.
    if not smoke:
        if normalized_speeds and set(normalized_speeds) == {"fast"}:
            # Allow generous timeout for subprocess-invoked runs that can load plugins
            # and perform slower startup on some machines.
            os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "120")
    speed_categories = normalized_speeds or None
    feature_map = _parse_feature_options(features)
    if feature_map:
        for name, enabled in feature_map.items():
            env_var = f"DEVSYNTH_FEATURE_{name.upper()}"
            os.environ[env_var] = "true" if enabled else "false"
        logger.info("Feature flags: %s", feature_map)

    _kwargs: dict[str, Any] = {}
    if marker is not None:
        # Map CLI --marker to the internal run_tests extra_marker parameter.
        _kwargs["extra_marker"] = marker

    success, output = run_tests(
        target,
        speed_categories,
        verbose,
        report,
        not no_parallel,
        segment,
        segment_size,
        maxfail,
        **_kwargs,
    )

    if output:
        ux_bridge.print(output)

    if success:
        ux_bridge.print("[green]Tests completed successfully[/green]")
        # Provide a friendly pointer to the HTML report location when requested.
        if report:
            try:
                from pathlib import Path as _Path

                report_root = _Path("test_reports")
                if report_root.exists():
                    ux_bridge.print(
                        "[green]HTML report available under[/green] "
                        + str(report_root.resolve())
                    )
                else:
                    ux_bridge.print(
                        "[yellow]Report flag was set but test_reports/ was not "
                        "found. The pytest run may have skipped report "
                        "generation.[/yellow]"
                    )
            except Exception:
                # Do not fail UX if filesystem inspection errs
                pass

        try:
            coverage_percent = enforce_coverage_threshold(exit_on_failure=False)
        except RuntimeError as exc:
            ux_bridge.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)
        else:
            ux_bridge.print(
                "[green]Coverage {0:.2f}% meets the {1:.0f}% threshold[/green]".format(
                    coverage_percent, DEFAULT_COVERAGE_THRESHOLD
                )
            )
            _emit_coverage_artifact_messages(ux_bridge)
    else:
        ux_bridge.print("[red]Tests failed[/red]")
        raise typer.Exit(code=1)
