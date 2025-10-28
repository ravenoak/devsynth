"""CLI command to execute shell commands in the MVU workflow."""

# Feature: MVU shell command execution

from __future__ import annotations

import subprocess
from typing import List, Optional

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def mvu_exec_cmd(command: list[str], *, bridge: UXBridge | None = None) -> int:
    """Run a shell command and forward its output.

    Args:
        command: Sequence representing the command and its arguments.
        bridge: Optional UX bridge for displaying output.

    Returns:
        Exit code from the executed command.
    """

    bridge = bridge or CLIUXBridge()
    logger.debug("Executing MVU command: %s", command)
    completed = subprocess.run(command, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    if output:
        bridge.print(output.rstrip())
    return completed.returncode
