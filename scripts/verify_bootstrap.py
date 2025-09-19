#!/usr/bin/env python3

"""Fail-fast verification of Taskfile and Poetry bootstrap requirements."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str = ""
    remediation: str | None = None


def run_command(cmd: Sequence[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def check_task() -> CheckResult:
    exe = shutil.which("task")
    if not exe:
        return CheckResult(
            name="go-task on PATH",
            ok=False,
            details="'task' executable not found on PATH",
            remediation="Run bash scripts/install_dev.sh to install go-task.",
        )

    code, out, err = run_command([exe, "--version"])
    if code != 0:
        details = err or out or "task --version returned a non-zero exit code"
        return CheckResult(
            name="go-task --version",
            ok=False,
            details=details,
            remediation="Reinstall go-task via bash scripts/install_dev.sh.",
        )

    version_line = out.splitlines()[0] if out else ""
    return CheckResult(
        name="go-task --version",
        ok=True,
        details=f"{version_line} ({exe})" if version_line else exe,
    )


def check_poetry_virtualenv() -> CheckResult:
    code, out, err = run_command(["poetry", "env", "info", "--path"])
    if code != 0 or not out:
        details = err or out or "poetry env info --path did not return a path"
        return CheckResult(
            name="Poetry virtualenv path",
            ok=False,
            details=details,
            remediation=(
                "Run bash scripts/install_dev.sh to recreate the Poetry environment."
            ),
        )

    venv_path = Path(out).resolve()
    if not venv_path.exists():
        return CheckResult(
            name="Poetry virtualenv path",
            ok=False,
            details=f"Virtualenv path {venv_path} does not exist",
            remediation=(
                "Run bash scripts/install_dev.sh to recreate the Poetry environment."
            ),
        )

    project_venv = Path(".venv")
    if not project_venv.exists():
        return CheckResult(
            name=".venv symlink or directory",
            ok=False,
            details=(
                ".venv is missing; expected Poetry to create an in-project virtualenv."
            ),
            remediation=(
                "Run bash scripts/install_dev.sh to recreate the Poetry environment."
            ),
        )

    project_resolved = project_venv.resolve()

    if venv_path != project_resolved:
        return CheckResult(
            name="Poetry virtualenv alignment",
            ok=False,
            details=(
                "Resolved Poetry env "
                f"({venv_path}) does not match .venv ({project_resolved})"
            ),
            remediation=(
                "Run bash scripts/install_dev.sh to refresh the in-project virtualenv."
            ),
        )

    return CheckResult(
        name="Poetry virtualenv alignment",
        ok=True,
        details=f"{project_venv} -> {project_resolved}",
    )


def check_devsynth_cli() -> CheckResult:
    code, out, err = run_command(["poetry", "run", "devsynth", "--help"])
    if code != 0:
        details = (
            err or out or "poetry run devsynth --help returned a non-zero exit code"
        )
        return CheckResult(
            name="poetry run devsynth --help",
            ok=False,
            details=details,
            remediation=(
                "Run bash scripts/install_dev.sh to reinstall project dependencies."
            ),
        )

    first_line = out.splitlines()[0] if out else "devsynth --help"
    return CheckResult(
        name="poetry run devsynth --help",
        ok=True,
        details=first_line,
    )


def print_result(result: CheckResult) -> None:
    status = "OK" if result.ok else "FAIL"
    print(f"[ {status:4} ] {result.name}")
    if result.details:
        print(f"    -> {result.details}")
    if not result.ok and result.remediation:
        print(f"    hint: {result.remediation}")


def main() -> int:
    checks = [check_task(), check_poetry_virtualenv(), check_devsynth_cli()]
    failures = [c for c in checks if not c.ok]

    print("Bootstrap verification\n" + "-" * 24)
    for check in checks:
        print_result(check)

    if failures:
        print("\nEnvironment verification failed.", file=sys.stderr)
        return 1

    print("\nEnvironment verification succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
