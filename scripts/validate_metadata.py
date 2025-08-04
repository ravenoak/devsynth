"""Deprecated metadata validation script.

This script is deprecated. Use the ``devsynth validate-metadata`` CLI command
instead of calling this module directly.
"""

from __future__ import annotations

import argparse

from devsynth.application.cli.commands import validate_metadata_cmd


def main() -> None:
    """Parse arguments and invoke the new CLI metadata validator."""

    parser = argparse.ArgumentParser(
        description=(
            "Deprecated wrapper for metadata validation. Use 'devsynth "
            "validate-metadata' instead."
        )
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Directory containing Markdown files to validate",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Single Markdown file to validate",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    validate_metadata_cmd.validate_metadata_cmd(
        directory=args.directory,
        file=args.file,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
