"""Central definitions for CLI command export names.

This module captures the mapping between attribute names exposed on
``devsynth.application.cli`` / ``devsynth.application.cli.cli_commands`` and the
command slugs registered in :data:`~devsynth.application.cli.registry.COMMAND_REGISTRY`.

By centralising this mapping we ensure that runtime exports, typing stubs, and
tests that stub or introspect CLI commands stay in sync.
"""

from __future__ import annotations

from typing import Mapping

# NOTE: ``Mapping`` is used instead of ``dict`` to communicate the intent that
# consumers should treat this structure as read-only.
COMMAND_ATTRIBUTE_TO_SLUG: Mapping[str, str] = {
    # Extra commands
    "align_cmd": "align",
    "completion_cmd": "completion",
    "init_cmd": "init",
    "run_tests_cmd": "run-tests",
    "testing_cmd": "testing",
    "edrr_cycle_cmd": "edrr-cycle",
    "security_audit_cmd": "security-audit",
    "reprioritize_issues_cmd": "reprioritize-issues",
    "atomic_rewrite_cmd": "atomic-rewrite",
    "mvuu_dashboard_cmd": "mvuu-dashboard",
    # Generation commands
    "spec_cmd": "spec",
    "test_cmd": "test",
    "code_cmd": "code",
    # Single-command modules
    "ingest_cmd": "ingest",
    # Interface commands
    "webapp_cmd": "webapp",
    "serve_cmd": "serve",
    "dbschema_cmd": "dbschema",
    "webui_cmd": "webui",
    "dpg_cmd": "dpg",
    # Metrics commands
    "alignment_metrics_cmd": "alignment-metrics",
    "test_metrics_cmd": "test-metrics",
    # Pipeline commands and aliases
    "run_pipeline_cmd": "run-pipeline",
    "run_cmd": "run",
    "gather_cmd": "gather",
    "refactor_cmd": "refactor",
    "inspect_cmd": "inspect",
    "inspect_config_cmd": "inspect-config",
    # Configuration commands
    "config_cmd": "config",
    "enable_feature_cmd": "enable-feature",
    # Diagnostics commands
    "doctor_cmd": "doctor",
    "check_cmd": "check",
    # Documentation commands
    "generate_docs_cmd": "generate-docs",
    # Validation commands
    "validate_manifest_cmd": "validate-manifest",
    "validate_metadata_cmd": "validate-metadata",
}

# Convenience tuple exposing the attribute names for quick iteration.
COMMAND_ATTRIBUTE_NAMES = tuple(COMMAND_ATTRIBUTE_TO_SLUG.keys())

# Convenience tuple exposing the registered command slugs.
COMMAND_SLUGS = tuple(COMMAND_ATTRIBUTE_TO_SLUG.values())


__all__ = [
    "COMMAND_ATTRIBUTE_TO_SLUG",
    "COMMAND_ATTRIBUTE_NAMES",
    "COMMAND_SLUGS",
]
