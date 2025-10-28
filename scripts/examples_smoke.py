#!/usr/bin/env python3
"""
Lightweight smoke checks for examples/ against the current CLI.

Goals (non-extra examples only):
- Ensure the CLI entrypoint is functional in a minimal install (no optional extras).
- Ensure example directories are structurally present and analyzable by the RepoAnalyzer via
  the "--analyze-repo" fast path, which avoids optional provider integrations.

This script is intentionally conservative: it does not execute long-running workflows or
network-dependent features. It focuses on catching obvious API/CLI drift and packaging issues
that would break the getting-started experience.

Exit status is non-zero if any smoke check fails.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from collections.abc import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"

# Examples that do not require optional extras or networked providers.
NON_EXTRA_EXAMPLES: list[str] = [
    "calculator",
    "init_example",
    "spec_example",
    "test_example",
    "code_example",
    "e2e_cli_example",
]


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def check_cli_help() -> None:
    rc, out, err = run(
        [sys.executable, "-m", "devsynth.cli", "--help"]
    )  # argparse/typer help
    # Accept either the argparse header string or the Typer header string
    if rc != 0 or (
        "DevSynth command line interface" not in out and "DevSynth CLI" not in out
    ):
        sys.stderr.write("ERROR: CLI --help failed or unexpected output.\n")
        sys.stderr.write(out + "\n" + err)
        raise SystemExit(1)


def analyze_example(example_path: Path) -> None:
    if not example_path.exists():
        sys.stderr.write(f"ERROR: Missing example path: {example_path}\n")
        raise SystemExit(1)

    # Use the fast RepoAnalyzer path to avoid optional extras
    rc, out, err = run(
        [sys.executable, "-m", "devsynth.cli", "--analyze-repo", str(example_path)]
    )
    if rc != 0:
        sys.stderr.write(f"ERROR: Repo analysis failed for {example_path}.\n")
        sys.stderr.write(out + "\n" + err)
        raise SystemExit(1)


def select_examples(names: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for name in names:
        p = EXAMPLES_DIR / name
        paths.append(p)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run examples smoke checks")
    parser.add_argument(
        "--examples",
        nargs="*",
        default=NON_EXTRA_EXAMPLES,
        help="Specific example folder names to check (defaults to non-extra set)",
    )
    args = parser.parse_args(argv)

    check_cli_help()

    failures = []
    for path in select_examples(args.examples):
        try:
            analyze_example(path)
            print(f"OK: analyzed {path.relative_to(REPO_ROOT)}")
        except SystemExit as e:
            failures.append((path, e.code or 1))
        except Exception as e:  # defensive
            sys.stderr.write(f"ERROR: Unexpected exception for {path}: {e}\n")
            failures.append((path, 1))

    if failures:
        sys.stderr.write("\nSummary of failures:\n")
        for p, code in failures:
            sys.stderr.write(f" - {p.relative_to(REPO_ROOT)} (exit {code})\n")
        return 1

    print("All example smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
