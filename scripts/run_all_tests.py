"""Deprecated test runner wrapper.

This script is deprecated in favor of the ``devsynth run-tests`` CLI command.
It simply forwards all arguments to that command.
"""

from __future__ import annotations

import subprocess
import sys
import warnings


def main() -> int:
    """Invoke the ``devsynth run-tests`` CLI command with passed arguments."""
    warnings.warn(
        "scripts/run_all_tests.py is deprecated; use 'devsynth run-tests' instead.",
        DeprecationWarning,
    )
    result = subprocess.run(
        [
            "devsynth",
            "run-tests",
            *sys.argv[1:],
        ]
    )
    return result.returncode


if __name__ == "__main__":  # pragma: no cover - script entry
    sys.exit(main())
