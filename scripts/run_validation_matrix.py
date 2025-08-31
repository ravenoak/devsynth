#!/usr/bin/env python3
"""
DevSynth validation helper: orchestrates a minimal subset of validation commands and
captures outputs as evidence under diagnostics/.

This script is intentionally lightweight and does not attempt to run the full matrix.
It focuses on high-signal, low-cost steps that unblock checklist items by producing
standardized artifacts you can attach to notes:
- pytest --collect-only (Section 1.2, 8.1 baseline discovery)
- scripts/verify_test_markers.py --report (Task 4.2 progress)

It also prints guidance for:
- Task 3.5 LM Studio 3× stability subset
- Section 8 matrix runs for unit/integration/behavior fast suites

Usage:
  poetry run python scripts/run_validation_matrix.py

Artifacts:
  diagnostics/pytest_collect_<timestamp>.txt
  diagnostics/verify_test_markers_<timestamp>.txt
  test_reports/test_markers_report.json (from the verifier)
  diagnostics/validation_next_steps_<timestamp>.txt (guidance echo)
"""
from __future__ import annotations

import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
TEST_REPORTS = ROOT / "test_reports"


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%dT%H%M%S")


def _run(cmd: list[str], outfile: Path) -> int:
    """Run a command, teeing stdout/stderr to outfile."""
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with outfile.open("w", encoding="utf-8") as f:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=ROOT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            f.write(line)
        return proc.wait()


def main() -> int:
    DIAG.mkdir(parents=True, exist_ok=True)
    TEST_REPORTS.mkdir(parents=True, exist_ok=True)

    ts = _ts()

    # 1) pytest --collect-only (baseline discovery)
    collect_out = DIAG / f"pytest_collect_{ts}.txt"
    print(f"[validation] Running pytest --collect-only → {collect_out}")
    rc_collect = _run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"], collect_out
    )

    # 2) verify test markers (full report)
    markers_out = DIAG / f"verify_test_markers_{ts}.txt"
    print(f"[validation] Running verify_test_markers.py --report → {markers_out}")
    rc_markers = _run(
        [
            sys.executable,
            "scripts/verify_test_markers.py",
            "--report",
            "--report-file",
            str(TEST_REPORTS / "test_markers_report.json"),
        ],
        markers_out,
    )

    # 3) Guidance for next steps (LM Studio stability and Section 8 matrix)
    guidance = f"""
Next steps (run locally to capture evidence for pending tasks):

Task 3.5 (LM Studio enabled stability, 3× runs, no-parallel, maxfail=1):
  # Ensure extras and env per docs/tasks.md §3.4 first
  poetry install --with dev --extras "tests llm"
  export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10
  export DEVSYNTH_LMSTUDIO_RETRIES=1
  task tests:lmstudio-stability

Section 8 matrix (baseline + fast suites):
  task tests:collect              # Baseline discovery artifact
  poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
  poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel
  poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --smoke

Segmented medium/slow (examples):
  poetry run devsynth run-tests --target unit-tests --speed=medium --segment --segment-size 50 --no-parallel
  poetry run devsynth run-tests --target unit-tests --speed=slow --segment --segment-size 50 --no-parallel
""".strip()

    guidance_file = DIAG / f"validation_next_steps_{ts}.txt"
    guidance_file.write_text(guidance + "\n", encoding="utf-8")
    print("[validation] Guidance written to", guidance_file)

    # Overall return code: non-zero if any of the above failed.
    rc = 0
    for r in (rc_collect, rc_markers):
        if r != 0:
            rc = r
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
