"""Compatibility layer exposing CLI commands for testing.

This module mirrors the command registration performed by the real CLI while
providing a few utility helpers that tests can use directly.  In particular it
offers a small progress-wrapper and access to the enhanced help text used by
the Typer application.
"""

from __future__ import annotations

from typing import Callable, cast

from devsynth.core import workflows

init_project = workflows.init_project

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge

# Expose a module-level bridge for tests to monkeypatch.
# Tests expect `devsynth.application.cli.cli_commands.bridge` to exist.
bridge: UXBridge = CLIUXBridge()

from ._command_exports import COMMAND_ATTRIBUTE_NAMES, COMMAND_ATTRIBUTE_TO_SLUG
from .commands import (
    config_cmds,
    diagnostics_cmds,
    documentation_cmds,
    extra_cmds,
    generation_cmds,
    interface_cmds,
    metrics_cmds,
    pipeline_cmds,
)
from .commands import spec_cmd as _spec_module
from .commands import (
    validation_cmds,
)
from .help import get_all_commands_help, get_command_help
from .progress import ProgressManager
from .registry import COMMAND_REGISTRY
from .utils import _check_services

generate_specs = _spec_module.generate_specs
_spec_module.generate_specs = generate_specs


CommandCallable = Callable[..., object]


def _registered_command(slug: str) -> CommandCallable:
    """Return the callable registered for ``slug``.

    Raises:
        RuntimeError: If the command slug is missing from the registry. This
            signals a programming error where the command module was not
            imported prior to exposing the compatibility shim used in tests.
    """

    try:
        return COMMAND_REGISTRY[slug]
    except KeyError as exc:  # pragma: no cover - defensive guardrail
        raise RuntimeError(f"CLI command '{slug}' is not registered") from exc


def create_progress(
    description: str,
    total: int = 100,
    *,
    bridge: UXBridge | None = None,
) -> ProgressIndicator:
    """Create a progress indicator for tests.

    Args:
        description: Description shown to the user.
        total: Total units of work.
        bridge: Optional bridge implementation.  Defaults to the CLI bridge.

    Returns:
        A :class:`~devsynth.interface.ux_bridge.ProgressIndicator` instance.
    """

    active_bridge = (
        bridge or cast(UXBridge | None, globals().get("bridge")) or CLIUXBridge()
    )
    manager = ProgressManager(active_bridge)
    # Use a fixed task id since tests typically track a single progress bar
    return manager.create_progress("task", description, total=total)


def show_help(command: str | None = None) -> str:
    """Return formatted help text for the CLI or a specific command."""

    return get_command_help(command) if command else get_all_commands_help()


align_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["align_cmd"])
completion_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["completion_cmd"]
)
init_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["init_cmd"])
run_tests_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["run_tests_cmd"]
)
edrr_cycle_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["edrr_cycle_cmd"]
)
security_audit_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["security_audit_cmd"]
)
reprioritize_issues_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["reprioritize_issues_cmd"]
)
atomic_rewrite_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["atomic_rewrite_cmd"]
)
mvuu_dashboard_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["mvuu_dashboard_cmd"]
)
spec_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["spec_cmd"])
test_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["test_cmd"])
code_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["code_cmd"])
ingest_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["ingest_cmd"]
)
webapp_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["webapp_cmd"]
)
serve_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["serve_cmd"])
dbschema_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["dbschema_cmd"]
)
webui_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["webui_cmd"])
dpg_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["dpg_cmd"])
alignment_metrics_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["alignment_metrics_cmd"]
)
test_metrics_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["test_metrics_cmd"]
)
run_pipeline_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["run_pipeline_cmd"]
)
run_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["run_cmd"])
gather_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["gather_cmd"]
)
refactor_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["refactor_cmd"]
)
inspect_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["inspect_cmd"]
)
inspect_config_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["inspect_config_cmd"]
)
config_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["config_cmd"]
)
enable_feature_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["enable_feature_cmd"]
)
doctor_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["doctor_cmd"]
)
check_cmd: CommandCallable = _registered_command(COMMAND_ATTRIBUTE_TO_SLUG["check_cmd"])
generate_docs_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["generate_docs_cmd"]
)
validate_manifest_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["validate_manifest_cmd"]
)
validate_metadata_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["validate_metadata_cmd"]
)


__all__ = [
    "workflows",
    "generate_specs",
    "_check_services",
    "create_progress",
    "show_help",
    "get_command_help",
    "get_all_commands_help",
] + list(COMMAND_ATTRIBUTE_NAMES)
