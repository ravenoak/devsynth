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

    # Disable xdist by default to avoid KeyError crashes from ``-n auto``.
    if "--no-parallel" not in args:
        args.append("--no-parallel")

    result = subprocess.run(
        ["devsynth", "run-tests", *args], capture_output=True, text=True
    )

    # Echo the output from the underlying command
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)

    if result.returncode != 0:
        failing = sorted(
            {
                line[line.find("tests/") :].split("::", 1)[0].split()[0]
                for line in result.stdout.splitlines()
                if "tests/" in line and (" FAILED" in line or " ERROR" in line)
            }
        )
        if failing:
            print("Failing modules:")
            for module in failing:
                print(f"- {module}")

    return result.returncode


if __name__ == "__main__":  # pragma: no cover - script entry
    sys.exit(main())
