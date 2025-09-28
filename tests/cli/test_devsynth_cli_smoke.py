"""Smoke checks that the DevSynth CLI entry points remain available. ReqID: CLI-SMOKE-001"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.cli
@pytest.mark.fast
def test_devsynth_module_help_invocation() -> None:
    """ReqID: CLI-SMOKE-001."""

    proc = subprocess.run(
        ["poetry", "run", "python", "-m", "devsynth", "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, (
        "`poetry run python -m devsynth --help` failed\n"
        f"stdout:\n{proc.stdout}\n"
        f"stderr:\n{proc.stderr}"
    )
