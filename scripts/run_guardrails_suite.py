#!/usr/bin/env python3
"""
Run DevSynth guardrail tools (format/lint/type/security) and save outputs under diagnostics/.

Usage examples:
  poetry run python scripts/run_guardrails_suite.py             # run all tools
  poetry run python scripts/run_guardrails_suite.py --only black isort
  poetry run python scripts/run_guardrails_suite.py --continue-on-error

This helper aligns with docs/plan.md and .junie/guidelines.md:
- Minimal dependencies
- Evidence-first: writes outputs to diagnostics/guardrails_<tool>_<timestamp>.txt
- Non-intrusive: does not modify files; it only runs checks
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

# Tools and their Poetry-invoked commands
TOOLS = {
    "black": ["black", "--check", "."],
    "isort": ["isort", "--check-only", "."],
    "flake8": ["flake8", "src/", "tests/"],
    "mypy": ["mypy", "src/devsynth"],
    "bandit": ["bandit", "-r", "src/devsynth", "-x", "tests"],
    "safety": ["safety", "check", "--full-report"],
}


def _timestamp() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%dT%H%M%S")


def _ensure_diagnostics_dir() -> Path:
    d = Path("diagnostics")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run_tool(
    tool: str, args: List[str], diagnostics_dir: Path, use_poetry: bool = True
) -> Tuple[int, Path]:
    ts = _timestamp()
    outfile = diagnostics_dir / f"guardrails_{tool}_{ts}.txt"
    cmd = (["poetry", "run"] if use_poetry else []) + args
    # Capture both stdout and stderr into the same file for convenience
    with outfile.open("w", encoding="utf-8") as f:
        f.write(f"$ {' '.join(cmd)}\n\n")
        f.flush()
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    return proc.returncode, outfile


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run DevSynth guardrail tools and save diagnostics outputs."
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help=f"Subset of tools to run from: {', '.join(TOOLS.keys())}",
    )
    parser.add_argument(
        "--no-poetry",
        action="store_true",
        help="Run tools without 'poetry run' (assumes tools are on PATH).",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue running remaining tools even if one fails; exit with aggregated non-zero code if any failed.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])
    selected = list(TOOLS.keys()) if not ns.only else ns.only

    invalid = [t for t in selected if t not in TOOLS]
    if invalid:
        print(
            f"Invalid tool(s): {', '.join(invalid)}. Valid: {', '.join(TOOLS.keys())}",
            file=sys.stderr,
        )
        return 2

    diagnostics_dir = _ensure_diagnostics_dir()

    results: List[Tuple[str, int, Path]] = []
    any_fail = False

    for tool in selected:
        cmd = TOOLS[tool]
        rc, out = _run_tool(
            tool, [cmd[0], *cmd[1:]], diagnostics_dir, use_poetry=not ns.no_poetry
        )
        results.append((tool, rc, out))
        status = "OK" if rc == 0 else f"FAIL (exit {rc})"
        print(f"{tool:7s} -> {status} | log: {out}")
        if rc != 0:
            any_fail = True
            if not ns.continue_on_error:
                break

    print("\nSummary:")
    for tool, rc, out in results:
        status = "OK" if rc == 0 else f"FAIL (exit {rc})"
        print(f"- {tool:7s}: {status} | {out}")

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
