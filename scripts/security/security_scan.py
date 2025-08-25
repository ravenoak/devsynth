#!/usr/bin/env python3
"""
Run security scans (Bandit & Safety) locally, producing JSON outputs and a brief summary.

Usage:
  poetry run python scripts/security/security_scan.py [--strict]

Options:
  --strict   Exit non-zero if any issues are found (default: non-strict).

Notes:
- Designed to align with DevSynth guidelines (.junie/guidelines.md) and be CI-friendly.
- Outputs:
  - bandit.json
  - safety.json
  - summary printed to stdout
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> int:
    try:
        print(f"$ {' '.join(cmd)}")
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        return res.returncode
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}", file=sys.stderr)
        return 127


def ensure_tools() -> None:
    # Best effort: verify bandit and safety are available
    missing = []
    for tool in ("bandit", "safety"):
        code = (
            run([sys.executable, "-m", tool, "--version"])
            if tool == "safety"
            else run(["bandit", "--version"])
        )
        if code not in (0, 2):  # bandit returns 2 for version sometimes
            missing.append(tool)
    if missing:
        print(
            "Missing tools: " + ", ".join(missing) + ".\n"
            "Install via: poetry run pip install bandit safety",
            file=sys.stderr,
        )


def main() -> int:
    strict = "--strict" in sys.argv

    ensure_tools()

    bandit_out = ROOT / "bandit.json"
    safety_out = ROOT / "safety.json"

    # Run Bandit
    bandit_code = run(["bandit", "-r", "src", "-f", "json", "-o", str(bandit_out)])
    # Run Safety (prefer key if set)
    env = os.environ.copy()
    safety_cmd = [sys.executable, "-m", "safety", "check", "--full-report", "--json"]
    if env.get("SAFETY_API_KEY"):
        safety_cmd.insert(3, "--key")
        safety_cmd.insert(4, env["SAFETY_API_KEY"])
    safety_code = run(safety_cmd)
    if safety_code == 0:
        # safety prints to stdout; capture from run() not returned as file. Rerun capturing explicitly.
        res = subprocess.run(safety_cmd, cwd=ROOT, capture_output=True, text=True)
        try:
            safety_out.write_text(res.stdout)
        except Exception as e:
            print(f"Failed to write safety.json: {e}", file=sys.stderr)
    else:
        # still try to persist any output
        res = subprocess.run(safety_cmd, cwd=ROOT, capture_output=True, text=True)
        try:
            safety_out.write_text(res.stdout)
        except Exception:
            pass

    # Summarize
    def load_json(path: Path):
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    bandit_data = load_json(bandit_out)
    safety_data = load_json(safety_out)

    print("\n=== Security Scan Summary ===")
    if isinstance(bandit_data, dict):
        issues = len(bandit_data.get("results", []))
        print(f"Bandit: {issues} issues (see {bandit_out.name})")
    else:
        print("Bandit: no JSON output available")

    # Safety JSON format: list of issues or dict depending on version
    if isinstance(safety_data, list):
        print(f"Safety: {len(safety_data)} vulnerabilities (see {safety_out.name})")
    elif isinstance(safety_data, dict):
        vulns = safety_data.get("vulnerabilities")
        if isinstance(vulns, list):
            print(f"Safety: {len(vulns)} vulnerabilities (see {safety_out.name})")
        else:
            print("Safety: JSON parsed, format unexpected")
    else:
        print("Safety: no JSON output available")

    if strict:
        any_issues = False
        if isinstance(bandit_data, dict) and bandit_data.get("results"):
            any_issues = True
        if isinstance(safety_data, list) and safety_data:
            any_issues = True
        if isinstance(safety_data, dict) and safety_data.get("vulnerabilities"):
            any_issues = True
        return 1 if any_issues else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
