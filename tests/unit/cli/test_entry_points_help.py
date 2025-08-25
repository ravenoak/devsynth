import os
import subprocess
import sys
from importlib.metadata import entry_points

import pytest


@pytest.mark.smoke
def test_devsynth_help_module_invocation():
    # Invoke devsynth via module to avoid relying on installed console script
    proc = subprocess.run(
        [sys.executable, "-m", "devsynth", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    # Typer help usually contains these markers
    assert "Usage:" in proc.stdout or "Options:" in proc.stdout


def _console_script_targets():
    # Build a mapping of console script name -> module:func string
    eps = entry_points()
    # For Python 3.12, entry_points returns an EntryPoints object; group() still works
    try:
        console = eps.select(group="console_scripts")
    except AttributeError:
        console = eps.get("console_scripts", [])
    return {ep.name: ep.value for ep in console}


@pytest.mark.smoke
def test_console_scripts_declared():
    targets = _console_script_targets()
    assert "devsynth" in targets
    assert "mvuu-dashboard" in targets
    assert targets["devsynth"].startswith(
        "devsynth.adapters.cli.typer_adapter"
    ), targets["devsynth"]
    assert targets["mvuu-dashboard"].startswith(
        "devsynth.application.cli.commands.mvuu_dashboard_cmd"
    ), targets["mvuu-dashboard"]


@pytest.mark.smoke
def test_mvuu_dashboard_help_via_module():
    # Run the command module with --help; argparse will print help and exit(0)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "devsynth.application.cli.commands.mvuu_dashboard_cmd",
            "--help",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0
    assert "mvuu-dashboard" in proc.stdout or "usage:" in proc.stdout.lower()
