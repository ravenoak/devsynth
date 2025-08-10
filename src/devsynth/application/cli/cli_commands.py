"""Compatibility layer exposing CLI commands for testing.

This module mirrors the command registration performed by the real CLI while
providing a few utility helpers that tests can use directly.  In particular it
offers a small progress-wrapper and access to the enhanced help text used by
the Typer application.
"""

from __future__ import annotations

from devsynth.core import workflows

init_project = workflows.init_project

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

from .commands import (
    config_cmds,
    diagnostics_cmds,
    extra_cmds,
    generation_cmds,
    interface_cmds,
    pipeline_cmds,
)
from .commands import spec_cmd as _spec_module
from .help import get_all_commands_help, get_command_help
from .progress import ProgressManager
from .registry import COMMAND_REGISTRY
from .utils import _check_services

generate_specs = _spec_module.generate_specs
_spec_module.generate_specs = generate_specs


def create_progress(
    description: str,
    total: int = 100,
    *,
    bridge: UXBridge | None = None,
):
    """Create a progress indicator for tests.

    Args:
        description: Description shown to the user.
        total: Total units of work.
        bridge: Optional bridge implementation.  Defaults to the CLI bridge.

    Returns:
        A :class:`~devsynth.interface.ux_bridge.ProgressIndicator` instance.
    """

    bridge = bridge or CLIUXBridge()
    manager = ProgressManager(bridge)
    # Use a fixed task id since tests typically track a single progress bar
    return manager.create_progress("task", description, total=total)


def show_help(command: str | None = None) -> str:
    """Return formatted help text for the CLI or a specific command."""

    return get_command_help(command) if command else get_all_commands_help()


for _name, _cmd in COMMAND_REGISTRY.items():
    globals()[f"{_name.replace('-', '_')}_cmd"] = _cmd


__all__ = [
    "workflows",
    "generate_specs",
    "_check_services",
    "create_progress",
    "show_help",
    "get_command_help",
    "get_all_commands_help",
] + [f"{name.replace('-', '_')}_cmd" for name in COMMAND_REGISTRY]
