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
    """Invoke the ``devsynth run-tests`` CLI command with passed arguments.

    Accepts an optional ``--report`` flag to generate an HTML test report and coverage XML
    using pytest-html and pytest-cov. When ``--report`` is provided, this script will invoke
    pytest directly to ensure artifacts are produced, writing to:
      - reports/test_report.html
      - coverage.xml
    """
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

    # Handle optional HTML report path
    want_report = False
    if "--report" in args:
        want_report = True
        args = [a for a in args if a != "--report"]

    # Disable xdist by default to avoid KeyError crashes from ``-n auto``.
    if "--no-parallel" not in args:
        args.append("--no-parallel")

    if want_report:
        # Ensure reports directory exists
        import os
        from pathlib import Path

        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Build a pytest command that respects filter args while producing artifacts
        pytest_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--maxfail=1",
            "--disable-warnings",
            "--cov=src/devsynth",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
            f"--html={reports_dir / 'test_report.html'}",
            "--self-contained-html",
        ]
        # Pass through remaining args (markers, paths, etc.)
        pytest_cmd.extend(args)
        result = subprocess.run(pytest_cmd, capture_output=True, text=True)
    else:
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
