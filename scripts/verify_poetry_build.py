#!/usr/bin/env python3
"""
Verify that `poetry build` succeeds and artifacts install in a clean venv.

- Runs `poetry build` (wheel + sdist)
- Fails if the process returns non-zero or if any line contains the word
  "warning" case-insensitively.
- Creates a temporary virtual environment, installs the built wheel, and
  verifies that `devsynth --help` exits with code 0.

This script is intended to satisfy docs/tasks.md item 3.2.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP_ENV = ROOT / ".tmp_build_verify"


def run(
    cmd: list[str], env: dict[str, str] | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        check=False,
    )


def ensure_clean_tmp_env() -> Path:
    if TMP_ENV.exists():
        shutil.rmtree(TMP_ENV)
    TMP_ENV.mkdir(parents=True, exist_ok=True)
    # python -m venv .tmp_build_verify/venv
    venv_dir = TMP_ENV / "venv"
    proc = run([sys.executable, "-m", "venv", str(venv_dir)])
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        raise SystemExit("Failed to create virtualenv for build verification")
    return venv_dir


def venv_paths(venv_dir: Path) -> tuple[Path, dict[str, str]]:
    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    py = bin_dir / ("python.exe" if os.name == "nt" else "python")
    pip = bin_dir / ("pip.exe" if os.name == "nt" else "pip")
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(venv_dir)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    return pip, env


def main() -> int:
    # 1) Build
    proc = run(["poetry", "build"], cwd=ROOT)
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    has_warning = any(
        re.search(r"\bwarning\b", line, re.IGNORECASE) for line in out.splitlines()
    )

    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    if proc.returncode != 0:
        print("[verify_poetry_build] poetry build failed", file=sys.stderr)
        return proc.returncode

    if has_warning:
        print(
            "[verify_poetry_build] warnings detected during poetry build",
            file=sys.stderr,
        )
        return 2

    # 2) Find wheel
    dist_dir = ROOT / "dist"
    wheels = sorted(dist_dir.glob("*.whl"))
    if not wheels:
        print(
            "[verify_poetry_build] no wheel found under dist/ after build",
            file=sys.stderr,
        )
        return 3
    wheel = wheels[-1]

    # 3) Create temp venv and install wheel
    venv_dir = ensure_clean_tmp_env()
    pip, env = venv_paths(venv_dir)

    # Upgrade pip to improve compatibility
    proc = run([str(pip), "install", "--upgrade", "pip"], env=env)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return 4

    proc = run([str(pip), "install", str(wheel)], env=env)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return 5

    # 4) Verify CLI help
    proc = run(["devsynth", "--help"], env=env)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        print("[verify_poetry_build] installed CLI --help failed", file=sys.stderr)
        return 6

    print("[verify_poetry_build] poetry build and install verification succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
