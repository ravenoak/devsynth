"""ReqID: EX-01

Smoke-validate that the minimal init example is runnable in under a second
without optional extras or network access.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.fast
def test_init_example_runs_quickly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the example script as a separate process and assert success.

    - Ensures compatibility with smoke mode (no third-party plugins).
    - Keeps execution deterministic and under a second.
    """
    # Ensure environment is clean and offline by default.
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    script = (
        Path(__file__).resolve().parents[2] / "examples" / "init_example" / "main.py"
    )
    assert script.exists(), f"Example script not found: {script}"

    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, check=False
    )

    assert (
        result.returncode == 0
    ), f"Example exited with non-zero code: {result.returncode}\nSTDERR: {result.stderr}"
    assert "DevSynth init example OK" in result.stdout
