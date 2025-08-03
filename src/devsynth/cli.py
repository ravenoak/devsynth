#!/usr/bin/env python3
"""DevSynth CLI entry point.

This module primarily delegates to the Typer based CLI defined in
``devsynth.adapters.cli.typer_adapter``.  A lightweight ``--analyze-repo``
option is provided for invoking the :class:`RepoAnalyzer` directly from the
command line without loading the full CLI stack.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from devsynth.application.code_analysis.repo_analyzer import RepoAnalyzer
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    If ``--analyze-repo`` is supplied, the repository at the provided path is
    analysed and the resulting data is printed as JSON.  Otherwise the standard
    Typer CLI is executed.
    """

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--analyze-repo", metavar="PATH", help="Analyze a repository and output JSON data")
    args, remaining = parser.parse_known_args(argv)

    if args.analyze_repo:
        analyzer = RepoAnalyzer(args.analyze_repo)
        result: dict[str, Any] = analyzer.analyze()
        print(json.dumps(result, indent=2))
    else:
        from devsynth.adapters.cli.typer_adapter import run_cli

        run_cli()


if __name__ == "__main__":  # pragma: no cover - tested via integration test
    main()
