#!/usr/bin/env python3
# DEPRECATED: use `devsynth align` instead. This script will be removed in a future release.
"""Run the DevSynth alignment check as a pre-commit hook.

Deprecated: use ``devsynth align`` instead. This wrapper exists only for
backward compatibility and will be removed in a future release.

This script is a thin wrapper around the project's CLI alignment command. It
executes the same alignment logic to ensure consistent behaviour with the
``devsynth align`` command and exits with compatible status codes.
"""

from __future__ import annotations

import argparse
import sys

from devsynth.application.cli.commands import align_cmd


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the alignment wrapper."""
    parser = argparse.ArgumentParser(
        description="Check alignment between SDLC artifacts using DevSynth's CLI"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Path to the project directory to check (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from the alignment command",
    )
    return parser.parse_args()


def main() -> int:
    """Execute the alignment check and return the CLI's exit status."""
    args = parse_args()
    try:
        issues = align_cmd.check_alignment(path=args.path, verbose=args.verbose)
        align_cmd.display_issues(issues)
        return 0 if not issues else 1
    except Exception as exc:  # pragma: no cover - mirror CLI behaviour
        print(f"Error checking alignment: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
