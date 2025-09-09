"""ReqID: EX-02

Minimal e2e smoke tests for key CLI commands that run quickly and validate
messaging and exit codes without relying on third-party plugins.

Covers:
- devsynth doctor (quick mode)
- devsynth run-tests (inventory-only mode for fast exit)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.fast
def test_doctor_cli_quick_smoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run `devsynth doctor --quick` via Python module entrypoint and assert success.

    - Forces smoke-compatible environment (no third-party plugins, offline-by-default).
    - Uses a temporary CWD to avoid polluting the repo.
    """
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    # Ensure a temporary working directory to keep artifacts isolated
    cwd = tmp_path

    # Use the module entrypoint to avoid requiring console script install in the environment
    cmd = [sys.executable, "-m", "devsynth", "doctor", "--quick"]
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=False
    )

    assert (
        result.returncode == 0
    ), f"doctor --quick exited with non-zero code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    # Basic sanity: some output is produced
    assert result.stdout.strip() != ""


@pytest.mark.fast
def test_run_tests_cli_inventory_smoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run `devsynth run-tests --inventory` in smoke mode and assert inventory file is written.

    - Runs in an empty temp directory so inventory may be empty but the JSON artifact must exist.
    - Validates quick execution and non-error exit code for e2e CLI path.
    """
    # Smoke/offline environment
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    cwd = tmp_path
    report_dir = cwd / "test_reports"
    inventory_path = report_dir / "test_inventory.json"

    cmd = [
        sys.executable,
        "-m",
        "devsynth",
        "run-tests",
        "--smoke",
        "--speed",
        "fast",
        "--no-parallel",
        "--inventory",
        "--target",
        "unit-tests",
    ]

    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=False
    )

    assert (
        result.returncode == 0
    ), f"run-tests --inventory exited with non-zero code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    # File should exist and contain valid JSON structure
    assert inventory_path.exists(), f"Inventory file not found: {inventory_path}"
    data = json.loads(inventory_path.read_text())
    assert "generated_at" in data and "targets" in data
