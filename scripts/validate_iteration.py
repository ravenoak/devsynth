#!/usr/bin/env python3
"""
Validate the current iteration runtime per docs/plan.md and .junie/guidelines.md.
- Runs pytest collect-only, verify_test_markers report, devsynth doctor,
  and a fast unit lane in smoke mode.
- If DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true, also runs the enabled subset
  for LM Studio as described in docs/tasks.md (fast, no-parallel, maxfail=1).
- Saves minimal evidence under diagnostics/iteration_<timestamp>/.

Run via Poetry:
  poetry run python scripts/validate_iteration.py

This script is deterministic and avoids heavy plugins by using smoke mode for the test lane.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG_DIR = (
    ROOT / "diagnostics" / f"iteration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
DIAG_DIR.mkdir(parents=True, exist_ok=True)

ENV = os.environ.copy()
# Ensure offline/stub defaults are preserved unless user overrides.
ENV.setdefault("DEVSYNTH_OFFLINE", "true")
ENV.setdefault("DEVSYNTH_PROVIDER", "stub")
ENV.setdefault("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")


def run(cmd: list[str], outfile: Path) -> int:
    with outfile.open("w", encoding="utf-8") as f:
        print(f"$ {' '.join(cmd)}", file=f)
        proc = subprocess.run(
            cmd, stdout=f, stderr=subprocess.STDOUT, env=ENV, cwd=ROOT
        )
        return proc.returncode


results: dict[str, dict[str, int | str]] = {}

# 1) pytest collect-only
rc = run(
    ["poetry", "run", "pytest", "--collect-only", "-q"], DIAG_DIR / "collect_only.txt"
)
results["collect_only"] = {
    "rc": rc,
    "log": str((DIAG_DIR / "collect_only.txt").relative_to(ROOT)),
}

# 2) verify_test_markers report
report_path = ROOT / "test_reports" / "test_markers_report.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
rc = run(
    [
        "poetry",
        "run",
        "python",
        "scripts/verify_test_markers.py",
        "--report",
        "--report-file",
        str(report_path),
    ],
    DIAG_DIR / "verify_test_markers.txt",
)
results["verify_test_markers"] = {
    "rc": rc,
    "log": str((DIAG_DIR / "verify_test_markers.txt").relative_to(ROOT)),
    "report": str(report_path.relative_to(ROOT)),
}

# 3) devsynth doctor
rc = run(["poetry", "run", "devsynth", "doctor"], DIAG_DIR / "doctor.txt")
results["doctor"] = {"rc": rc, "log": str((DIAG_DIR / "doctor.txt").relative_to(ROOT))}

# 4) fast unit lane (smoke)
rc = run(
    [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--target",
        "unit-tests",
        "--speed=fast",
        "--no-parallel",
        "--smoke",
        "--maxfail=1",
    ],
    DIAG_DIR / "unit_fast_smoke.txt",
)
results["unit_fast_smoke"] = {
    "rc": rc,
    "log": str((DIAG_DIR / "unit_fast_smoke.txt").relative_to(ROOT)),
}

# 5) LM Studio subset if enabled
lm_enabled = ENV.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false").lower() == "true"
if lm_enabled:
    rc = run(
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
            "--marker",
            "requires_resource('lmstudio') and not slow",
            "--smoke",
        ],
        DIAG_DIR / "lmstudio_enabled_subset.txt",
    )
    results["lmstudio_enabled_subset"] = {
        "rc": rc,
        "log": str((DIAG_DIR / "lmstudio_enabled_subset.txt").relative_to(ROOT)),
    }
else:
    results["lmstudio_enabled_subset"] = {
        "rc": -1,
        "note": "skipped (resource flag false)",
    }

summary_path = DIAG_DIR / "SUMMARY.json"
with summary_path.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# Print concise summary and set exit code if any required steps failed.
required_keys = ["collect_only", "verify_test_markers", "doctor", "unit_fast_smoke"]
failed = [k for k in required_keys if results[k]["rc"] != 0]
print(json.dumps(results, indent=2))

sys.exit(1 if failed else 0)
