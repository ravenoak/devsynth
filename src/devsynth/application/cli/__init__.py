"""Application-level CLI facades that delegate into orchestration layer."""

from typing import Callable

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

# Import modules so they register their commands
from .commands import (
    config_cmds,
    diagnostics_cmds,
    documentation_cmds,
    extra_cmds,
    generation_cmds,
    interface_cmds,
    metrics_cmds,
    pipeline_cmds,
    validation_cmds,
)
from .commands.config_cmds import config_app
from .commands.inspect_code_cmd import inspect_code_cmd
from .ingest_cmd import ingest_cmd
from .registry import COMMAND_REGISTRY

from ._command_exports import COMMAND_ATTRIBUTE_TO_SLUG, COMMAND_ATTRIBUTE_NAMES


CommandCallable = Callable[..., object]


def _registered_command(slug: str) -> CommandCallable:
    """Return the callable registered for ``slug``."""

    try:
        return COMMAND_REGISTRY[slug]
    except KeyError as exc:  # pragma: no cover - defensive guardrail
        raise RuntimeError(f"CLI command '{slug}' is not registered") from exc


align_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["align_cmd"]
)
completion_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["completion_cmd"]
)
init_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["init_cmd"]
)
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
spec_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["spec_cmd"]
)
test_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["test_cmd"]
)
code_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["code_cmd"]
)
webapp_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["webapp_cmd"]
)
serve_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["serve_cmd"]
)
dbschema_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["dbschema_cmd"]
)
webui_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["webui_cmd"]
)
dpg_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["dpg_cmd"]
)
alignment_metrics_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["alignment_metrics_cmd"]
)
test_metrics_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["test_metrics_cmd"]
)
run_pipeline_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["run_pipeline_cmd"]
)
run_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["run_cmd"]
)
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
check_cmd: CommandCallable = _registered_command(
    COMMAND_ATTRIBUTE_TO_SLUG["check_cmd"]
)
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
    "config_app",
    "inspect_code_cmd",
    "ingest_cmd",
    "COMMAND_REGISTRY",
] + list(COMMAND_ATTRIBUTE_NAMES)
