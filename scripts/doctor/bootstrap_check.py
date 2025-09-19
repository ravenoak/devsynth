#!/usr/bin/env python3
"""Verify bootstrap prerequisites for local DevSynth workflows."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_command(cmd: Sequence[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def check_task() -> bool:
    task_exe = shutil.which("task")
    if not task_exe:
        message = (
            "[env:verify] 'task' executable not found on PATH. "
            "Run bash scripts/install_dev.sh."
        )
        print(message, file=sys.stderr)
        return False

    code, out, err = run_command([task_exe, "--version"])
    if code != 0:
        print(
            f"[env:verify] 'task --version' failed with exit code {code}",
            file=sys.stderr,
        )
        if out:
            print(out, file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
        return False

    first_line = out.splitlines()[0] if out else "task (no version output)"
    print(f"[env:verify] task available: {first_line}")
    return True


def check_poetry_env() -> tuple[bool, Path | None]:
    poetry_exe = shutil.which("poetry")
    if not poetry_exe:
        print("[env:verify] 'poetry' executable not found on PATH.", file=sys.stderr)
        return False, None

    code, out, err = run_command([poetry_exe, "env", "info", "--path"])
    if code != 0 or not out:
        print(
            f"[env:verify] 'poetry env info --path' failed with exit code {code}",
            file=sys.stderr,
        )
        if out:
            print(out, file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
        return False, None

    venv_path = Path(out.strip())
    if not venv_path.exists():
        print(
            f"[env:verify] Poetry virtualenv directory {venv_path} is missing.",
            file=sys.stderr,
        )
        return False, venv_path

    expected = REPO_ROOT / ".venv"
    if venv_path == expected:
        print(f"[env:verify] poetry virtualenv resolved to {venv_path}")
    else:
        print(
            "[env:verify] poetry virtualenv resolved to "
            f"{venv_path} (expected {expected})",
            file=sys.stderr,
        )
    return True, venv_path


def check_devsynth_cli(poetry_exe: str) -> bool:
    code, _, err = run_command([poetry_exe, "run", "devsynth", "--help"])
    if code != 0:
        print("[env:verify] 'poetry run devsynth --help' failed.", file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
        return False

    print("[env:verify] devsynth CLI available via 'poetry run devsynth --help'")
    return True


def main() -> int:
    ok = True

    if not check_task():
        ok = False

    poetry_exe = shutil.which("poetry")
    env_ok, venv_path = check_poetry_env()
    ok = ok and env_ok

    if poetry_exe and env_ok:
        if venv_path:
            devsynth_bin = venv_path / "bin" / "devsynth"
            if not devsynth_bin.exists():
                missing_msg = (
                    "[env:verify] warning: expected CLI entry point "
                    f"{devsynth_bin} is missing"
                )
                print(missing_msg, file=sys.stderr)
        if not check_devsynth_cli(poetry_exe):
            ok = False
    else:
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
