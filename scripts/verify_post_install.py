#!/usr/bin/env python3
"""Verify Poetry post-install invariants for DevSynth."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def ensure_poetry_env() -> Path:
    proc = run_command(["poetry", "env", "info", "--path"])
    if proc.returncode != 0:
        sys.stderr.write(
            "[post-install] 'poetry env info --path' failed with exit code"
            f" {proc.returncode}.\n"
        )
        if proc.stdout:
            sys.stderr.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                sys.stderr.write("\n")
        if proc.stderr:
            sys.stderr.write(proc.stderr)
            if not proc.stderr.endswith("\n"):
                sys.stderr.write("\n")
        raise SystemExit(proc.returncode or 1)

    path_str = proc.stdout.strip()
    if not path_str:
        sys.stderr.write("[post-install] poetry did not return a virtualenv path.\n")
        raise SystemExit(1)

    return Path(path_str)


def ensure_devsynth_cli(venv_path: Path) -> None:
    devsynth_executable = venv_path / "bin" / "devsynth"
    if not devsynth_executable.is_file():
        sys.stderr.write(
            f"[post-install] devsynth executable not found at {devsynth_executable}.\n"
        )
        raise SystemExit(1)

    proc = run_command(["poetry", "run", "devsynth", "--help"])
    if proc.returncode != 0:
        sys.stderr.write(
            "[post-install] 'poetry run devsynth --help' failed with exit code"
            f" {proc.returncode}.\n"
        )
        if proc.stdout:
            sys.stderr.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                sys.stderr.write("\n")
        if proc.stderr:
            sys.stderr.write(proc.stderr)
            if not proc.stderr.endswith("\n"):
                sys.stderr.write("\n")
        raise SystemExit(proc.returncode or 1)


def main() -> int:
    venv_path = ensure_poetry_env()
    print(f"[post-install] poetry virtualenv: {venv_path}")
    ensure_devsynth_cli(venv_path)
    print("[post-install] devsynth CLI is available via 'poetry run devsynth --help'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
