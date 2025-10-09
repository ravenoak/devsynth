#!/usr/bin/env python3
"""DevSynth CLI entry point.

See ``docs/specifications/cli_entrypoint.md`` for design details.

This module primarily delegates to the Typer based CLI defined in
``devsynth.adapters.cli.typer_adapter``.  A lightweight ``--analyze-repo``
option is provided for invoking the :class:`RepoAnalyzer` directly from the
command line without loading the full CLI stack.  The Typer application
exposes shell completion installation via ``--install-completion``.
"""

# Feature: CLI Entrypoint

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from typing import Any, cast

from typer import Typer as TyperApp

from devsynth.application.code_analysis.repo_analyzer import RepoAnalyzer
from devsynth.logger import setup_logging

logger = setup_logging(__name__)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    If ``--analyze-repo`` is supplied, the repository at the provided path is
    analysed and the resulting data is printed as JSON.  Otherwise the standard
    Typer CLI is executed.

    Examples:
        Analyze the current repository::

            devsynth --analyze-repo .
    """

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        add_help=False,
        description="DevSynth command line interface",
    )
    parser.add_argument(
        "--analyze-repo",
        metavar="PATH",
        help="Analyze a repository and output JSON data",
    )
    args: argparse.Namespace
    remaining: list[str]
    args, remaining = parser.parse_known_args(argv)

    if args.analyze_repo:
        # Ensure heavy Typer CLI stack is not imported/retained for this fast path.
        # Some test scenarios may have previously imported the CLI; clearing here
        # guarantees this code path does not rely on it and keeps import-time light.
        sys.modules.pop("devsynth.adapters.cli.typer_adapter", None)
        analyze_repo = cast(str, args.analyze_repo)
        analyzer = RepoAnalyzer(analyze_repo)
        result = analyzer.analyze()
        payload = {
            "dependencies": result.dependencies,
            "structure": result.structure,
        }
        print(json.dumps(payload, indent=2))
    else:
        from devsynth.application.cli.errors import handle_error
        from devsynth.interface.cli import CLIUXBridge

        if remaining and remaining[0] == "run-tests":
            try:
                from devsynth.application.cli.commands.run_tests_cmd import (
                    run_tests_cmd,
                )
            except ModuleNotFoundError as exc:  # pragma: no cover - optional deps
                msg = (
                    f"Missing optional dependency: {exc.name}. "
                    "Install the required provider package to enable this feature."
                )
                handle_error(CLIUXBridge(), msg)
                raise SystemExit(1)

            app = TyperApp(add_completion=False)
            app.command("run-tests")(run_tests_cmd)
            try:
                app_runner = cast(Callable[..., Any], app)
                app_runner(prog_name="devsynth", args=remaining)
            except Exception as err:  # pragma: no cover - defensive
                handle_error(CLIUXBridge(), err)
                raise SystemExit(1)
        else:
            try:
                module = importlib.import_module("devsynth.adapters.cli.typer_adapter")
                run_cli = cast(Callable[[], None], getattr(module, "run_cli"))
            except ModuleNotFoundError as exc:  # pragma: no cover - optional deps
                msg = (
                    f"Missing optional dependency: {exc.name}. "
                    "Install the required provider package to enable this feature."
                )
                handle_error(CLIUXBridge(), msg)
                raise SystemExit(1)

            try:
                run_cli()
            except ModuleNotFoundError as exc:  # pragma: no cover - optional deps
                msg = (
                    f"Missing optional dependency: {exc.name}. "
                    "Install the required provider package to enable this feature."
                )
                handle_error(CLIUXBridge(), msg)
                raise SystemExit(1)
            except Exception as err:  # pragma: no cover - defensive
                handle_error(CLIUXBridge(), err)
                raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover - tested via integration test
    main()
