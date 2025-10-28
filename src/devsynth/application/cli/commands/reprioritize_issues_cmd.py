"""CLI command to reprioritize open issues."""

from __future__ import annotations

from typing import Optional

from devsynth.application.issues import reprioritize_open_issues
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

bridge: UXBridge = CLIUXBridge()


def reprioritize_issues_cmd(*, bridge: UXBridge | None = None) -> None:
    """Recalculate priority fields for open issues."""
    ux_bridge = bridge or globals()["bridge"]
    counts = reprioritize_open_issues()
    for level, count in counts.items():
        ux_bridge.print(f"{level.title()}: {count}")
