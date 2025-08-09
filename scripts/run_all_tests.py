"""Deprecated test runner wrapper.

This script is deprecated in favor of the ``devsynth run-tests`` CLI command.
It simply forwards all arguments to that command.
"""

from __future__ import annotations

import json
import subprocess
import sys
import warnings


def main() -> int:
    """Invoke the ``devsynth run-tests`` CLI command with passed arguments."""
    warnings.warn(
        "scripts/run_all_tests.py is deprecated; use 'devsynth run-tests' instead.",
        DeprecationWarning,
    )

    # Convert legacy ``--features`` JSON option to new ``--feature`` flags
    args: list[str] = []
    itr = iter(sys.argv[1:])
    for arg in itr:
        if arg in {"--features", "-f"}:  # pragma: no cover - legacy path
            value = next(itr, "{}")
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                data = {}
            for name, enabled in data.items():
                args.extend(["--feature", f"{name}={enabled}"])
        elif arg.startswith("--features="):
            _, value = arg.split("=", 1)
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                data = {}
            for name, enabled in data.items():
                args.extend(["--feature", f"{name}={enabled}"])
        else:
            args.append(arg)

    result = subprocess.run(["devsynth", "run-tests", *args])
    return result.returncode


if __name__ == "__main__":  # pragma: no cover - script entry
    sys.exit(main())
