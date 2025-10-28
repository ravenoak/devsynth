#!/usr/bin/env python3
"""
Verify exit criteria by orchestrating key commands and capturing artifacts under diagnostics/.
This script is a convenience wrapper to help maintainers complete docs/tasks.md Task 20.
It does not enforce success; it records outcomes and writes a summary JSON.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

Command = tuple[list[str], str]  # (argv, artifact path for stdout tee)


def run_and_capture(cmd: list[str], artifact_path: str) -> int:
    p = Path(artifact_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as out:
        out.write(
            f"# Command: {' '.join(cmd)}\n# Started: {datetime.now(timezone.utc).isoformat()}\n\n"
        )
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            out.write(line)
        proc.wait()
        out.write(f"\n# Exit: {proc.returncode}\n")
        return proc.returncode


def append_exec_log(command: str, exit_code: int, artifacts: str, notes: str) -> None:
    subprocess.run(
        [
            "poetry",
            "run",
            "python",
            "scripts/append_exec_log.py",
            "--command",
            command,
            "--exit-code",
            str(exit_code),
            "--artifacts",
            artifacts,
            "--notes",
            notes,
        ],
        check=False,
    )


def main() -> int:
    diagnostics = Path("diagnostics")
    diagnostics.mkdir(exist_ok=True)

    steps: dict[str, Command] = {
        # Marker verification
        "marker_verification": (
            [
                "poetry",
                "run",
                "python",
                "scripts/verify_test_markers.py",
                "--report",
                "--report-file",
                "test_reports/test_markers_report.json",
            ],
            "diagnostics/verify_markers_stdout.txt",
        ),
        # Inventory
        "inventory": (
            ["poetry", "run", "devsynth", "run-tests", "--inventory"],
            "diagnostics/test_inventory_capture.txt",
        ),
        # Unit fast
        "unit_fast": (
            [
                "poetry",
                "run",
                "devsynth",
                "run-tests",
                "--target",
                "unit-tests",
                "--speed=fast",
                "--no-parallel",
                "--maxfail=1",
            ],
            "diagnostics/unit_fast.txt",
        ),
        # Integration fast
        "integration_fast": (
            [
                "poetry",
                "run",
                "devsynth",
                "run-tests",
                "--target",
                "integration-tests",
                "--speed=fast",
                "--no-parallel",
                "--maxfail=1",
            ],
            "diagnostics/integration_fast.txt",
        ),
        # Behavior fast
        "behavior_fast": (
            [
                "poetry",
                "run",
                "devsynth",
                "run-tests",
                "--target",
                "behavior-tests",
                "--speed=fast",
                "--no-parallel",
                "--maxfail=1",
            ],
            "diagnostics/behavior_fast.txt",
        ),
        # Offline/stub subset excludes resources
        "offline_subset": (
            [
                "poetry",
                "run",
                "devsynth",
                "run-tests",
                "--speed=fast",
                "-m",
                "not requires_resource('openai') and not requires_resource('lmstudio')",
                "--no-parallel",
                "--maxfail=1",
            ],
            "diagnostics/offline_fast_subset.txt",
        ),
        # Guardrails suite
        "guardrails": (
            [
                "poetry",
                "run",
                "python",
                "scripts/run_guardrails_suite.py",
                "--continue-on-error",
            ],
            "diagnostics/guardrails_suite_stdout.txt",
        ),
    }

    results: dict[str, Any] = {
        "started": datetime.now(timezone.utc).isoformat(),
        "steps": {},
    }
    overall_rc = 0
    artifacts: list[str] = []

    for name, (argv, artifact) in steps.items():
        rc = run_and_capture(argv, artifact)
        results["steps"][name] = {"rc": rc, "artifact": artifact}
        artifacts.append(artifact)
        overall_rc = overall_rc or rc

    # Write summary
    summary_path = diagnostics / "exit_criteria_summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Append exec log
    append_exec_log(
        command="python scripts/verify_exit_criteria.py",
        exit_code=overall_rc,
        artifacts=",".join(artifacts + [str(summary_path)]),
        notes="exit criteria verifier",
    )
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
