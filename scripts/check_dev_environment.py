#!/usr/bin/env python3
"""
Check development environment for DevSynth.
- Python 3.12+
- Poetry installed
- Optional: pre-commit installed
- Report helpful next steps to the contributor.

This script prints a non-zero exit code on critical failures, but tries to be
informative and self-contained. It does not modify the environment.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str = ""
    hint: str | None = None


def run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError as e:
        return 127, "", str(e)


def check_python() -> CheckResult:
    major, minor = sys.version_info[:2]
    ok = (major == 3 and minor >= 12) or (major > 3)
    return CheckResult(
        name="Python version >= 3.12",
        ok=ok,
        details=f"Detected Python {major}.{minor}",
        hint="Use pyenv or your system package manager to install Python 3.12+.",
    )


def check_poetry() -> CheckResult:
    poetry = shutil.which("poetry")
    if not poetry:
        return CheckResult(
            name="Poetry installed",
            ok=False,
            details="'poetry' not found on PATH",
            hint="See https://python-poetry.org/docs/ for installation instructions.",
        )
    code, out, _ = run([poetry, "--version"])
    return CheckResult(
        name="Poetry executable",
        ok=code == 0,
        details=out or "poetry --version failed",
    )


def check_precommit() -> CheckResult:
    exe = shutil.which("pre-commit")
    if not exe:
        return CheckResult(
            name="pre-commit installed (optional but recommended)",
            ok=False,
            details="'pre-commit' not found on PATH",
            hint="pipx install pre-commit or pip install pre-commit",
        )
    code, out, _ = run([exe, "--version"])
    return CheckResult(name="pre-commit executable", ok=code == 0, details=out)


def main() -> int:
    checks = [check_python(), check_poetry(), check_precommit()]

    # Optional extras summary (best-effort, no failures)
    extras = {
        "DEVSYNTH_PROPERTY_TESTING": os.getenv("DEVSYNTH_PROPERTY_TESTING", "false"),
    }

    print("DevSynth Development Environment Check\n" + "-" * 44)
    failures = 0
    for c in checks:
        status = "OK" if c.ok else "FAIL"
        print(f"[ {status:4} ] {c.name}")
        if c.details:
            print(f"    -> {c.details}")
        if not c.ok and c.hint:
            print(f"    hint: {c.hint}")
        if not c.ok and c.name.startswith("Python"):
            failures += 1
        if not c.ok and c.name.startswith("Poetry"):
            failures += 1

    print("\nEnvironment flags (informational):")
    print(json.dumps(extras, indent=2))

    if failures:
        print(
            "\nOne or more critical checks failed. Please address them and retry.",
            file=sys.stderr,
        )
        return 1

    print("\nEnvironment looks good. Next steps:")
    print("  1) poetry install --with dev,docs --all-extras")
    print("  2) poetry shell")
    print("  3) pre-commit install && pre-commit autoupdate (optional)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
