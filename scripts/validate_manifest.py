# DEPRECATED: use `devsynth validate-manifest` instead. This script will be
# removed in the next major release. See docs/policies/deprecation_policy.md for
# details.
"""Wrapper for validating DevSynth project manifests.

DEPRECATED: use ``devsynth validate-manifest`` instead. This script remains for
backward compatibility and will be removed in the next major release. Older
automation that invoked ``scripts/validate_manifest.py`` directly should
transition to the CLI command. The heavy lifting now lives in
:mod:`devsynth.application.cli.commands.validate_manifest_cmd`, so this file
simply forwards arguments to that command. See
``docs/policies/deprecation_policy.md`` for the deprecation schedule.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# Ensure the src directory is on the Python path so we can import devsynth.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import importlib.util

# Load the validate_manifest_cmd module directly to avoid importing the entire CLI
# package and its heavy dependencies.
_module_path = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "commands"
    / "validate_manifest_cmd.py"
)
_spec = importlib.util.spec_from_file_location("validate_manifest_cmd", _module_path)
validate_manifest_cmd = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(validate_manifest_cmd)

from rich.console import Console


class _SimpleBridge:
    """Minimal bridge implementing the interface expected by the command."""

    def __init__(self) -> None:
        self.console = Console()

    def print(self, message: str, **kwargs) -> None:  # type: ignore[override]
        self.console.print(message, **kwargs)


def main() -> None:
    """Parse arguments and run the ``validate-manifest`` command."""

    parser = argparse.ArgumentParser(
        description="Validate a DevSynth project manifest using the built-in CLI command."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        help="Path to the manifest file (.devsynth/project.yaml or manifest.yaml)",
    )
    parser.add_argument(
        "schema",
        nargs="?",
        help="Path to the manifest schema JSON file",
    )
    args = parser.parse_args()

    kwargs: dict[str, str | None] = {}
    if args.manifest:
        kwargs["manifest_path"] = args.manifest
    if args.schema:
        kwargs["schema_path"] = args.schema

    # The validate_manifest_cmd function handles output and status reporting.
    validate_manifest_cmd.validate_manifest_cmd(bridge=_SimpleBridge(), **kwargs)


if __name__ == "__main__":
    main()
