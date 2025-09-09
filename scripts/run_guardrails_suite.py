#!/usr/bin/env python3
"""
Run Black/isort/Flake8/mypy/Bandit/Safety in sequence and write artifacts under diagnostics/.
Exits non-zero if any tool fails unless --continue-on-error is passed.
Also appends a summary entry to diagnostics/exec_log.txt via scripts/append_exec_log.py.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str], outfile: Path) -> int:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    with outfile.open("w", encoding="utf-8") as f:
        f.write(f"# Command: {' '.join(cmd)}\n# Started: {started}\n\n")
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            f.write(line)
        proc.wait()
        rc = proc.returncode
        f.write(f"\n# Exit: {rc}\n")
        return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    diagnostics = Path("diagnostics")

    steps: list[tuple[list[str], Path]] = [
        (["poetry", "run", "black", "--check", "."], diagnostics / "black_check.txt"),
        (
            ["poetry", "run", "isort", "--check-only", "."],
            diagnostics / "isort_check.txt",
        ),
        (
            [
                "poetry",
                "run",
                "flake8",
                "--max-line-length",
                "88",
                "--extend-ignore",
                "E203,W503",
                "src/",
                "tests/",
            ],
            diagnostics / "flake8.txt",
        ),
        (["poetry", "run", "mypy", "src/devsynth"], diagnostics / "mypy.txt"),
        (
            ["poetry", "run", "bandit", "-r", "src/devsynth", "-x", "tests"],
            diagnostics / "bandit.txt",
        ),
        (
            ["poetry", "run", "safety", "check", "--full-report"],
            diagnostics / "safety.txt",
        ),
    ]

    overall_rc = 0
    for cmd, out in steps:
        rc = run(cmd, out)
        if rc != 0:
            overall_rc = rc if overall_rc == 0 else overall_rc
            if not args.continue_on_error:
                # append exec log summary before exiting early
                try:
                    artifacts = ",".join(str(p) for _, p in steps)
                    subprocess.run(
                        [
                            "poetry",
                            "run",
                            "python",
                            "scripts/append_exec_log.py",
                            "--command",
                            "python scripts/run_guardrails_suite.py",
                            "--exit-code",
                            str(overall_rc or rc),
                            "--artifacts",
                            artifacts,
                            "--notes",
                            "guardrails suite (early exit)",
                        ],
                        check=False,
                    )
                except Exception:
                    pass
                return overall_rc

    # Append exec log at the end with overall status
    try:
        artifacts = ",".join(str(p) for _, p in steps)
        subprocess.run(
            [
                "poetry",
                "run",
                "python",
                "scripts/append_exec_log.py",
                "--command",
                "python scripts/run_guardrails_suite.py",
                "--exit-code",
                str(overall_rc),
                "--artifacts",
                artifacts,
                "--notes",
                "guardrails suite",
            ],
            check=False,
        )
    except Exception:
        pass

    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
