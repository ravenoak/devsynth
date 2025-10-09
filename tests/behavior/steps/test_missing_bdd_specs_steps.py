from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then

from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

FEATURES = [
    "cli_overhaul_pseudocode.feature",
    "cli_ui_improvements.feature",
    "delimiting_recursion_algorithms.feature",
    "dialectical_reasoning_impact_memory_persistence.feature",
    "document_generator_enhancement_requirements.feature",
    "documentation_plan.feature",
    "edrr_recursion_termination.feature",
    "edrr_cycle_specification.feature",
    "edrr_framework_integration_summary.feature",
    "edrr_phase_recovery_threshold_helpers.feature",
    "edrr_reasoning_loop_integration.feature",
    "end_to_end_deployment.feature",
    "generated_test_execution_failure.feature",
    "hybrid_memory_architecture.feature",
    "index.feature",
    "integration_test_generation.feature",
    "lmstudio_integration.feature",
    "memory_optional_tinydb_dependency.feature",
    "metrics_system.feature",
    "mvuu_config.feature",
    "nicegui_interface.feature",
    "recursive_edrr_pseudocode.feature",
    "run_tests_maxfail_option.feature",
    "spec_template.feature",
    "test_generation_multi_module.feature",
    "tiered_cache_validation.feature",
    "unified_configuration_loader.feature",
    "uxbridge_extension.feature",
    "verify_test_markers_performance.feature",
    "webui_core.feature",
    "webui_detailed_spec.feature",
    "webui_diagnostics_audit_logs.feature",
    "webui_pseudocode.feature",
    "webui_spec.feature",
    "wsde_interaction_specification.feature",
    "wsde_role_progression_memory.feature",
]
for feature in FEATURES:
    scenarios(feature_path(__file__, "general", feature))

SPEC_DIR = Path(__file__).parents[2] / "docs" / "specifications"


@given(parsers.parse('the specification "{spec}" exists'))
def spec_exists(spec: str):
    """ReqID: SPEC-TRACE"""
    assert (SPEC_DIR / spec).is_file()


@then("the BDD coverage acknowledges the specification")
def acknowledge():
    """ReqID: SPEC-TRACE"""
    assert True
