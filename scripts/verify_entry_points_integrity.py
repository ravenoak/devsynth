#!/usr/bin/env python3
"""
Verify that declared entry points in pyproject.toml resolve to callable targets
and that the primary CLI can produce help output without executing external
systems.

This script does not require network and should run in any environment where
DevSynth is installed (editable or sdist/wheel). It supports Packaging Sanity
(Task 29) by providing a quick local integrity check for entry points.

Checks performed:
- Import and call devsynth.adapters.cli.typer_adapter:run_cli with --help
  using Typer's CliRunner to avoid launching a real process.
- Import mvuu-dashboard entry point target and ensure it is callable.

Exit codes:
- 0 on success
- non-zero on failure with a concise diagnostic message
"""
from __future__ import annotations

import sys
from collections.abc import Callable


def _fail(msg: str) -> None:
    print(f"[entry-points] ERROR: {msg}")
    sys.exit(1)


def _ok(msg: str) -> None:
    print(f"[entry-points] OK: {msg}")


def _import_callable(path: str) -> Callable[..., object]:
    """Import a function given a fully-qualified path like module:attr.attr2."""
    if ":" not in path:
        _fail(f"Invalid entry point path (missing colon): {path}")
    mod_name, attr_path = path.split(":", 1)
    try:
        mod = __import__(
            mod_name, fromlist=["__dummy__"]
        )  # fromlist to get submodule attrs
    except Exception as e:  # pragma: no cover - simple utility
        _fail(f"Failed to import module '{mod_name}': {e}")
    obj = mod
    for part in attr_path.split("."):
        try:
            obj = getattr(obj, part)
        except AttributeError as e:
            _fail(f"Failed to resolve '{attr_path}' in '{mod_name}': {e}")
    if not callable(obj):
        _fail(f"Resolved object is not callable: {path}")
    return obj  # type: ignore[no-any-return]


def _check_devsynth_cli() -> None:
    # Verify run_cli is importable and produces help
    run_cli = _import_callable("devsynth.adapters.cli.typer_adapter:run_cli")

    # Use Typer CliRunner to avoid forking processes
    try:
        from typer.testing import CliRunner
    except Exception as e:  # pragma: no cover - depends on dev extra
        _fail(f"Typer testing utilities not available: {e}")

    runner = CliRunner()
    try:
        result = runner.invoke(run_cli, ["--help"])  # type: ignore[arg-type]
    except Exception as e:
        _fail(f"Invoking CLI help raised an exception: {e}")
    if result.exit_code != 0:
        _fail(
            f"CLI help returned non-zero exit code: {result.exit_code}\n{result.output}"
        )
    if "Usage:" not in result.output and "devsynth" not in result.output:
        _fail("CLI help output does not look correct")
    _ok("devsynth CLI entry point resolved and --help executed")


def _check_mvuu_dashboard() -> None:
    # Ensure the function is importable and callable; do not actually run it.
    mvuu = _import_callable(
        "devsynth.application.cli.commands.mvuu_dashboard_cmd:mvuu_dashboard_cmd"
    )
    # Perform a trivial attribute check to ensure callability
    if not hasattr(mvuu, "__call__"):
        _fail("mvuu-dashboard target is not callable")
    _ok("mvuu-dashboard entry point target resolved and callable")


def main() -> None:
    _check_devsynth_cli()
    _check_mvuu_dashboard()
    print("[entry-points] All checks passed")


if __name__ == "__main__":
    main()
