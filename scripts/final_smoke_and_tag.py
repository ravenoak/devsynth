#!/usr/bin/env python3
"""
Final smoke and optional tag script.

This script orchestrates the final smoke steps described in docs/tasks.md #19:
  1) Run: poetry run pytest (default fast subset per pytest.ini)
  2) Run: poetry run pytest tests/integration/ and tests/behavior/
  3) If all pass and gates are satisfied, execute Taskfile release:prep, and (optionally)
     tag v<version> and push the tag.

Safety by default:
  - Dry-run by default: shows what it would do. Use --execute for real runs.
  - Tagging is disabled by default; use --tag to create the git tag and --push to push it.

Usage:
  poetry run python scripts/final_smoke_and_tag.py [--execute] [--tag] [--push] [--tag-prefix v]

Notes:
  - Requires go-task ('task') available in PATH.
  - Reads version from pyproject.toml and constructs tag as <tag-prefix><version> (default: 'v0.1.0a1' -> 'v0.1.0a1').
  - Aligns with docs/roadmap/release_plan.md (lines 28–32) and Taskfile release:prep.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None


def run(cmd: list[str], check: bool = True, dry_run: bool = False) -> int:
    print("$", " ".join(cmd))
    if dry_run:
        return 0
    proc = subprocess.run(cmd)
    if check and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc.returncode


def read_version(pyproject_path: Path) -> str:
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    if tomllib is None:
        raise RuntimeError("tomllib not available in this Python runtime")
    data = tomllib.loads(pyproject_path.read_text())
    # Poetry style
    try:
        version = data["tool"]["poetry"]["version"]
    except Exception as e:
        raise KeyError(f"Failed to read version from {pyproject_path}: {e}")
    if not isinstance(version, str) or not version:
        raise ValueError("Invalid version in pyproject.toml")
    return version


def main() -> int:
    ap = argparse.ArgumentParser(description="Final smoke and optional tag")
    ap.add_argument(
        "--execute", action="store_true", help="Execute commands (not dry-run)"
    )
    ap.add_argument(
        "--tag",
        action="store_true",
        help="Create git tag after successful release:prep",
    )
    ap.add_argument(
        "--push", action="store_true", help="Push the created tag to origin"
    )
    ap.add_argument("--tag-prefix", default="v", help="Prefix for git tag (default: v)")
    args = ap.parse_args()

    dry = not args.execute

    # 1/2: Final smoke (uses pytest.ini defaults)
    # If poetry is configured, prefer 'poetry run', but tests can be invoked directly via 'poetry run pytest'
    run(["poetry", "run", "pytest"], dry_run=dry)
    run(["poetry", "run", "pytest", "tests/integration/"], dry_run=dry)
    run(["poetry", "run", "pytest", "tests/behavior/"], dry_run=dry)

    # 3: release:prep via Taskfile
    # This builds, verifies markers, audits, and checks release gating.
    run(["task", "release:prep"], dry_run=dry)

    # Tagging & pushing
    if args.tag:
        version = read_version(Path("pyproject.toml"))
        tag = f"{args.tag_prefix}{version}"
        run(["git", "tag", tag], dry_run=dry)
        if args.push:
            run(["git", "push", "origin", tag], dry_run=dry)
        else:
            print(
                f"[info] Tag created locally (dry_run={dry}). Use --push to push to origin."
            )
    else:
        print("[info] Tagging disabled (use --tag to enable).")

    print("[final_smoke_and_tag] Completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
