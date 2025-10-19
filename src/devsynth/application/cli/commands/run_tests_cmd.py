"""CLI command to run DevSynth tests.

Wraps :func:`devsynth.testing.run_tests` to provide a `devsynth run-tests`
command. This command mirrors the options exposed by the underlying helper.

Example:
    `devsynth run-tests --target unit-tests --speed fast`
"""

from __future__ import annotations

import os
import shlex

import typer

# Ensure sitecustomize is loaded for Python 3.12+ compatibility patches
import sitecustomize  # noqa: F401
from devsynth.config.provider_env import ProviderEnv
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.observability.metrics import increment_counter

# Import run_tests functions with explicit assignment to ensure they're available
from devsynth.testing.run_tests import (
    COVERAGE_HTML_DIR,
    COVERAGE_JSON_PATH,
    PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE,
    PYTEST_COV_PLUGIN_MISSING_MESSAGE,
    _coverage_threshold,
    collect_tests_with_cache,
    coverage_artifacts_status,
    enforce_coverage_threshold,
    ensure_pytest_asyncio_plugin_env,
    ensure_pytest_bdd_plugin_env,
    ensure_pytest_cov_plugin_env,
    pytest_cov_support_status,
    run_tests,
)

# Ensure imported functions are accessible in the module namespace
# The import above should make these available, but we verify they're accessible

logger = DevSynthLogger(__name__)
DEFAULT_BRIDGE: UXBridge = CLIUXBridge()


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


def _parse_pytest_addopts(addopts: str | None) -> list[str]:
    """Parse ``PYTEST_ADDOPTS`` into discrete tokens."""

    if not addopts or not addopts.strip():
        return []
    try:
        return shlex.split(addopts)
    except ValueError:
        # Fall back to a naive split when quoting is imbalanced; pytest will
        # still receive the original string and surface the parsing error.
        return addopts.split()


def _addopts_has_plugin(tokens: list[str], plugin: str) -> bool:
    """Check whether a ``-p`` plugin directive exists for the given plugin."""

    for index, token in enumerate(tokens):
        if token == "-p" and index + 1 < len(tokens) and tokens[index + 1] == plugin:
            return True
        if token.startswith("-p") and token[2:] == plugin:
            return True
    return False


def _coverage_instrumentation_disabled(tokens: list[str]) -> bool:
    """Return ``True`` when coverage instrumentation is explicitly disabled."""

    if "--no-cov" in tokens:
        return True
    if _addopts_has_plugin(tokens, "no:cov"):
        return True
    if _addopts_has_plugin(tokens, "no:pytest_cov"):
        return True
    return False


def _coverage_instrumentation_status() -> tuple[bool, str | None]:
    """Determine whether pytest-cov instrumentation is active."""

    return pytest_cov_support_status(os.environ)


def run_tests_cmd(
    target: str = typer.Option(
        "all-tests",
        "--target",
        help="Test target to run",
    ),
    # Set PYTHONPATH to ensure sitecustomize is loaded early for Python
    # 3.12+
    # compatibility
    _pythonpath: str | None = typer.Option(
        None,
        hidden=True,
        help="Internal option to set PYTHONPATH for sitecustomize loading",
    ),
    speeds: list[str] | None = typer.Option(
        None,
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the pytest command without executing tests",
    ),
    features: list[str] | None = typer.Option(
        None,
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
    bridge: object | None = typer.Option(None, hidden=True),
) -> None:
    """Run DevSynth test suites.

    For workflow and performance details see
    ``docs/analysis/run_tests_workflow.md``.
    """

    # Set PYTHONPATH to ensure sitecustomize is loaded for Python 3.12+
    # compatibility
    src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if src_path not in current_pythonpath:
        os.environ["PYTHONPATH"] = f"{src_path}:{current_pythonpath}"

    if isinstance(bridge, UXBridge):
        ux_bridge = bridge
    else:
        ux_bridge = DEFAULT_BRIDGE

    # Typer guarantees booleans for "inventory", but tests may invoke this
    # function directly. Normalize parameters defensively for that scenario.
    inventory = bool(inventory)

    # Extract actual values from OptionInfo objects
    actual_speeds = (
        speeds.default if speeds is not None and hasattr(speeds, "default") else speeds
    )
    actual_features = (
        features.default
        if features is not None and hasattr(features, "default")
        else features
    )

    normalized_speed_inputs = list(actual_speeds or [])
    normalized_feature_inputs = list(actual_features or [])

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

    normalized_speeds = [s.lower() for s in normalized_speed_inputs]
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

    # Smoke mode: minimize plugin surface and disable xdist, but still
    # generate coverage artifacts
    if smoke:
        os.environ["DEVSYNTH_SMOKE_MODE"] = "1"  # Set smoke mode flag
        os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        addopts_value = os.environ.get("PYTEST_ADDOPTS", "").strip()
        tokens = _parse_pytest_addopts(addopts_value) if addopts_value else []
        # Ensure xdist is disabled
        if "-p" not in tokens or "no:xdist" not in " ".join(tokens):
            addopts_value = ("-p no:xdist " + addopts_value).strip()
        # When plugin autoloading is disabled, explicitly load pytest-cov so
        # coverage artifacts can be produced
        if os.environ.get(
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD"
        ) == "1" and not _addopts_has_plugin(tokens, "pytest_cov"):
            addopts_value = ("-p pytest_cov " + addopts_value).strip()
            tokens = _parse_pytest_addopts(addopts_value)
        # Ensure the coverage gate doesn't fail smoke runs while still
        # producing artifacts
        if "--cov-fail-under" not in addopts_value:
            addopts_value = (addopts_value + " --cov-fail-under=0").strip()
        # Ensure pytest-asyncio operates in auto mode to avoid async test
        # failures with newer versions
        if "--asyncio-mode" not in addopts_value:
            addopts_value = (addopts_value + " --asyncio-mode=auto").strip()
        os.environ["PYTEST_ADDOPTS"] = addopts_value
        no_parallel = True
        # In smoke mode, default to fast tests when no explicit speeds are provided.
        if not normalized_speeds:
            normalized_speeds = ["fast"]
        # Enforce a conservative per-test timeout for smoke runs unless overridden
        os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "30")
        if dry_run:
            ux_bridge.print(
                (
                    "[cyan]Smoke dry-run enabled — previewing fast lane with "
                    "plugins disabled and xdist off.[/cyan]"
                )
            )

    # Optimize inner subprocess validation runs used by tests: disable plugins
    # and parallelism to avoid timeouts and reduce startup overhead, but only
    # when explicitly indicated by tests.
    if os.environ.get("DEVSYNTH_INNER_TEST") == "1":
        os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        existing_addopts = os.environ.get("PYTEST_ADDOPTS", "")
        # Prepend to ensure our flags take effect
        os.environ["PYTEST_ADDOPTS"] = ("-p no:xdist " + existing_addopts).strip()
        no_parallel = True

    # Even in smoke mode, inject essential plugins explicitly when autoload is
    # disabled
    coverage_plugin_injected = ensure_pytest_cov_plugin_env(os.environ)
    bdd_plugin_injected = ensure_pytest_bdd_plugin_env(os.environ)
    asyncio_plugin_injected = ensure_pytest_asyncio_plugin_env(os.environ)

    # In smoke mode, force the coverage gate to be non-fatal while preserving
    # artifact generation
    if smoke:
        existing_addopts = os.environ.get("PYTEST_ADDOPTS", "")
        if "--cov-fail-under" not in existing_addopts:
            os.environ["PYTEST_ADDOPTS"] = (
                existing_addopts + " --cov-fail-under=0"
            ).strip()

    if coverage_plugin_injected:
        message = (
            "[cyan]-p pytest_cov appended to PYTEST_ADDOPTS "
            "because plugin autoloading is disabled[/cyan]"
        )
        logger.info(
            (
                "CLI appended -p pytest_cov to PYTEST_ADDOPTS to enforce "
                "coverage instrumentation"
            ),
            extra={"pytest_addopts": os.environ.get("PYTEST_ADDOPTS", "")},
        )
        ux_bridge.print(message)
    if bdd_plugin_injected:
        message = (
            "[cyan]-p pytest_bdd.plugin appended to PYTEST_ADDOPTS "
            "because plugin autoloading is disabled[/cyan]"
        )
        logger.info(
            (
                "CLI appended -p pytest_bdd.plugin to PYTEST_ADDOPTS to "
                "preserve pytest-bdd hooks"
            ),
            extra={"pytest_addopts": os.environ.get("PYTEST_ADDOPTS", "")},
        )
        ux_bridge.print(message)
    if asyncio_plugin_injected:
        message = (
            "[cyan]-p pytest_asyncio appended to PYTEST_ADDOPTS "
            "because plugin autoloading is disabled[/cyan]"
        )
        logger.info(
            (
                "CLI appended -p pytest_asyncio to PYTEST_ADDOPTS to preserve "
                "async test support"
            ),
            extra={"pytest_addopts": os.environ.get("PYTEST_ADDOPTS", "")},
        )
        ux_bridge.print(message)

    coverage_enabled_initial, coverage_skip_reason_initial = (
        _coverage_instrumentation_status()
    )
    if not coverage_enabled_initial:
        detail = coverage_skip_reason_initial or (
            "pytest-cov instrumentation is required for coverage enforcement."
        )
        if dry_run:
            ux_bridge.print(
                (
                    "[yellow]Dry run: coverage instrumentation unavailable: "
                    f"{detail}[/yellow]"
                )
            )
        else:
            ux_bridge.print(
                f"[red]Coverage instrumentation unavailable: {detail}[/red]"
            )
            if (
                coverage_skip_reason_initial == PYTEST_COV_PLUGIN_MISSING_MESSAGE
                or not smoke
            ):
                raise typer.Exit(code=1)

    # For explicit fast-only runs (and not smoke), apply a slightly looser timeout
    # to catch stalls while avoiding flakiness on slower machines.
    if not smoke:
        if normalized_speeds and set(normalized_speeds) == {"fast"}:
            # Allow generous timeout for subprocess-invoked runs that can load plugins
            # and perform slower startup on some machines.
            os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "120")
    speed_categories = normalized_speeds or None
    feature_map = _parse_feature_options(normalized_feature_inputs)
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
        extra_marker=marker,
        dry_run=dry_run,
    )

    if output:
        ux_bridge.print(output)

    if dry_run:
        if success:
            ux_bridge.print(
                (
                    "[yellow]Dry run complete — no tests executed. Rerun "
                    "without --dry-run to execute suites.[/yellow]"
                )
            )
            return
        raise typer.Exit(code=1)

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

        coverage_enabled, skip_reason = _coverage_instrumentation_status()
        if smoke:
            details: list[str] = []
            if coverage_enabled:
                details.append("coverage data collected for diagnostics")
            elif skip_reason:
                details.append(skip_reason)
            notice = "; ".join(details)
            suffix = f" ({notice})" if notice else ""
            ux_bridge.print(
                "[yellow]Coverage enforcement skipped in smoke mode"
                f"{suffix}. Run fast+medium profiles before enforcing the "
                f"{_coverage_threshold():.0f}% gate.[/yellow]"
            )

            if coverage_enabled:
                _emit_coverage_artifact_messages(ux_bridge)
        elif not coverage_enabled:
            detail = f" ({skip_reason})" if skip_reason else ""
            message = (
                "[yellow]Coverage enforcement skipped: pytest-cov instrumentation "
                "disabled"
                f"{detail}.[/yellow]"
            )
            ux_bridge.print(message)

            if skip_reason == PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE:
                remediation = (
                    "[red]Coverage artifacts were not generated because pytest-cov was "
                    "disabled. Unset PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 or append "
                    "'-p pytest_cov' to PYTEST_ADDOPTS, then rerun the command.[/red]"
                )
                ux_bridge.print(remediation)
                raise typer.Exit(code=1)
        else:
            artifacts_ok, artifact_issue = coverage_artifacts_status()
            if not artifacts_ok:
                detail = f" ({artifact_issue})" if artifact_issue else ""
                remediation = (
                    "Ensure pytest-cov is active for this session. Remove "
                    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 or supply '-p pytest_cov' when "
                    "using custom PYTEST_ADDOPTS."
                )
                ux_bridge.print(
                    "[red]Coverage artifacts missing or empty"
                    f"{detail}. {remediation}[/red]"
                )
                raise typer.Exit(code=1)

            try:
                coverage_percent = enforce_coverage_threshold(exit_on_failure=False)
            except RuntimeError as exc:
                ux_bridge.print(f"[red]{exc}[/red]")
                raise typer.Exit(code=1)
            else:
                ux_bridge.print(
                    (
                        "[green]Coverage {:.2f}% meets the {:.0f}% threshold[/green]"
                    ).format(coverage_percent, _coverage_threshold())
                )
                _emit_coverage_artifact_messages(ux_bridge)
    else:
        ux_bridge.print("[red]Tests failed[/red]")
        raise typer.Exit(code=1)
