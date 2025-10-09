"""Step definitions for the EDRR Coordinator feature.

ReqID: FR-40
"""

from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "edrr_coordinator.feature"))
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Tuple

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.edrr.manifest_parser import ManifestParser
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def context():
    """Fixture to provide a context object for storing test state between steps."""

    class Context:

        def __init__(self):
            self.memory_manager = None
            self.wsde_team = None
            self.code_analyzer = None
            self.ast_transformer = None
            self.prompt_manager = None
            self.documentation_manager = None
            self.edrr_coordinator = None
            self.task = None
            self.temp_dir = None
            self.manifest_path = None
            self.final_report = None
            self.execution_traces = None

    return Context()


def _unwrap_wsde_team(team):
    """Return the underlying WSDE team if a proxy is used."""

    return getattr(team, "_team", team)


@given("the EDRR coordinator is initialized")
def edrr_coordinator_initialized(context):
    """Initialize the EDRR coordinator with actual implementations."""
    from devsynth.application.memory.adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter,
    )

    memory_adapter = TinyDBMemoryAdapter()
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam(name="TestEdrrCoordinatorStepsTeam")
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager, storage_path="tests/fixtures/docs"
    )
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager,
        enable_enhanced_logging=True,
    )


@given("the memory system is available")
def memory_system_available(context):
    """Make the memory system available."""
    assert context.memory_manager is not None
    assert context.edrr_coordinator.memory_manager is context.memory_manager


@given("the WSDE team is available")
def wsde_team_available(context):
    """Make the WSDE team available."""
    assert context.wsde_team is not None
    coordinator_team = _unwrap_wsde_team(context.edrr_coordinator.wsde_team)
    assert coordinator_team is context.wsde_team


@given("the AST analyzer is available")
def ast_analyzer_available(context):
    """Make the AST analyzer available."""
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None
    assert context.edrr_coordinator.code_analyzer is context.code_analyzer
    assert context.edrr_coordinator.ast_transformer is context.ast_transformer


@given("the prompt manager is available")
def prompt_manager_available(context):
    """Make the prompt manager available."""
    assert context.prompt_manager is not None
    assert context.edrr_coordinator.prompt_manager is context.prompt_manager


@given("the documentation manager is available")
def documentation_manager_available(context):
    """Make the documentation manager available."""
    assert context.documentation_manager is not None
    assert (
        context.edrr_coordinator.documentation_manager is context.documentation_manager
    )


@given("a coordinator managing Expand, Differentiate, Refine, and Retrospect phases")
def coordinator_ready_for_all_phases(context):
    """Ensure a coordinator is available for full-cycle execution."""

    if context.edrr_coordinator is None:
        edrr_coordinator_initialized(context)


@given("an initial context")
def initial_cycle_context(context):
    """Provide a default task used for end-to-end cycle execution."""

    context.task = {
        "id": "edrr-cycle-task",
        "description": "Coordinate EDRR phases end-to-end",
        "complexity_score": 3,
    }


@when("the coordinator executes an EDRR cycle")
def coordinator_executes_full_cycle(context):
    """Run the coordinator through each EDRR phase."""

    task = getattr(context, "task", None) or {
        "id": "edrr-cycle-task",
        "description": "Coordinate EDRR phases",
        "complexity_score": 3,
    }
    context.edrr_coordinator.start_cycle(task)
    context.executed_phases = []

    for _ in range(10):
        phase = context.edrr_coordinator.current_phase
        if phase is None:
            break
        context.executed_phases.append(phase)
        context.edrr_coordinator.execute_current_phase()
        if phase == Phase.RETROSPECT:
            break


@then("the coordinator reports completion")
def coordinator_reports_completion(context):
    """Verify the coordinator marked the retrospection phase as complete."""

    retrospect_results = context.edrr_coordinator.results.get(Phase.RETROSPECT.name, {})
    assert retrospect_results.get("completed") is True
    assert retrospect_results.get("phase_complete") is True


@then("the final context contains results from all phases")
def final_context_contains_all_phases(context):
    """Ensure aggregated outputs reference each EDRR phase."""

    aggregated = context.edrr_coordinator.results.get("AGGREGATED", {})
    expected_phases = {"expand", "differentiate", "refine", "retrospect"}
    assert expected_phases.issubset(aggregated.keys()), aggregated.keys()
    for phase in expected_phases:
        assert aggregated.get(phase), f"Aggregated context missing data for {phase}"


@given("agents produce conflicting outcomes during the Refine phase")
def refine_phase_conflicts(context):
    """Seed conflicting results to exercise micro-cycle reconciliation."""

    if context.edrr_coordinator is None:
        edrr_coordinator_initialized(context)

    conflict_task = {
        "id": "refine-conflict",
        "description": "Resolve conflicting implementations",
        "complexity_score": 4,
    }
    context.edrr_coordinator.start_cycle(conflict_task)
    context.edrr_coordinator.execute_current_phase()
    context.edrr_coordinator.execute_current_phase()

    assert context.edrr_coordinator.current_phase == Phase.REFINE

    conflict_results = {
        "implementation": {"variants": ["solution_a", "solution_b"]},
        "micro_cycle_results": {},
        "phase_complete": False,
        "quality_score": 0.35,
    }
    context.edrr_coordinator.results[Phase.REFINE.name] = conflict_results
    context.conflicting_refine_results = conflict_results


@when("the coordinator launches a micro cycle to reconcile differences")
def coordinator_launches_micro_cycle(context):
    """Invoke a micro cycle and aggregate the reconciled solution."""

    micro_cycle_output = {
        "resolved_solution": {
            "id": "consensus-plan",
            "contributors": ["solution_a", "solution_b"],
        },
        "quality_score": 0.92,
        "context": {"notes": "Unified implementation produced by micro cycle"},
    }
    aggregated = context.edrr_coordinator._aggregate_micro_cycle_results(
        Phase.REFINE, 1, micro_cycle_output
    )
    aggregated["phase_complete"] = True
    aggregated["quality_score"] = micro_cycle_output["quality_score"]

    refine_results = context.edrr_coordinator.results[Phase.REFINE.name]
    refine_results["aggregated_results"] = aggregated["aggregated_results"]
    refine_results["phase_complete"] = True
    refine_results["quality_score"] = micro_cycle_output["quality_score"]
    refine_results.setdefault("micro_cycle_results", {})[
        "iteration_1"
    ] = micro_cycle_output

    context.micro_cycle_results = aggregated
    context.edrr_coordinator._aggregate_results()


@then("the cycle terminates with a single coherent context")
def cycle_terminates_with_coherent_context(context):
    """Verify micro-cycle aggregation resolved the conflicts."""

    refine_results = context.edrr_coordinator.results.get(Phase.REFINE.name, {})
    aggregated = refine_results.get("aggregated_results", {})
    resolved = aggregated.get("resolved_solution")
    assert resolved is not None
    assert resolved.get("id") == "consensus-plan"

    overall = context.edrr_coordinator.results.get("AGGREGATED", {})
    if "refine" in overall:
        consensus = overall["refine"].get("resolved_solution")
        if consensus is not None:
            assert consensus.get("id") == "consensus-plan"


@then("no further phase transitions occur")
def no_additional_phase_transitions(context):
    """Ensure the coordinator remains in the Refine phase after reconciliation."""

    assert context.edrr_coordinator.current_phase == Phase.REFINE
    refine_results = context.edrr_coordinator.results.get(Phase.REFINE.name, {})
    assert refine_results.get("phase_complete") is True
    assert context.edrr_coordinator.manual_next_phase is None


@when(parsers.parse('I start the EDRR cycle with a task to "{task_description}"'))
def start_edrr_cycle(context, task_description):
    """Start the EDRR cycle with a task."""
    context.task = {"id": "task-123", "description": task_description}
    context.edrr_coordinator.start_cycle(context.task)


@given(parsers.parse('the "{phase_name}" phase has completed for a task'))
def phase_completed(context, phase_name):
    """Set up a completed phase."""
    context.task = {"id": "task-123", "description": "analyze a Python file"}
    context.edrr_coordinator.start_cycle(context.task)
    phase = Phase[phase_name.upper()]
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Capture stored items for verification. ReqID: FR-40"""
        test_storage.setdefault(edrr_phase, []).append(
            {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        )
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = store_method_succeeds
    try:
        if (
            phase == Phase.EXPAND
            or phase == Phase.DIFFERENTIATE
            or phase == Phase.REFINE
            or phase == Phase.RETROSPECT
        ):
            context.edrr_coordinator.results[Phase.EXPAND] = {
                "completed": True,
                "approaches": [
                    {
                        "id": "approach-1",
                        "description": "First approach",
                        "code": "def approach1(): pass",
                    },
                    {
                        "id": "approach-2",
                        "description": "Second approach",
                        "code": "def approach2(): pass",
                    },
                ],
            }
            context.edrr_coordinator.progress_to_phase(Phase.EXPAND)
        if (
            phase == Phase.DIFFERENTIATE
            or phase == Phase.REFINE
            or phase == Phase.RETROSPECT
        ):
            context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
                "completed": True,
                "evaluation": {
                    "selected_approach": {
                        "id": "approach-1",
                        "description": "Selected approach",
                        "code": "def example(): pass",
                    }
                },
            }
            context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        if phase == Phase.REFINE or phase == Phase.RETROSPECT:
            context.edrr_coordinator.results[Phase.REFINE] = {
                "completed": True,
                "implementation": {
                    "code": "def example(): return 'Hello, World!'",
                    "description": "Implemented solution",
                },
            }
            context.edrr_coordinator.progress_to_phase(Phase.REFINE)
        if phase == Phase.RETROSPECT:
            context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method
    if (
        phase not in context.edrr_coordinator.results
        or not context.edrr_coordinator.results[phase].get("completed", False)
    ):
        context.edrr_coordinator.results[phase] = {
            "completed": True,
            "outputs": [{"type": "approach", "content": "Sample approach"}],
        }


@when(parsers.parse('the coordinator progresses to the "{phase_name}" phase'))
def progress_to_phase(context, phase_name):
    """Progress to the next phase."""
    context.edrr_coordinator.progress_to_phase(Phase[phase_name.upper()])


@then(parsers.parse('the coordinator should enter the "{phase_name}" phase'))
def verify_phase(context, phase_name):
    """Verify the coordinator has entered the specified phase."""
    assert context.edrr_coordinator.current_phase == Phase[phase_name.upper()]


@then(
    parsers.parse(
        'the coordinator should store the task in memory with EDRR phase "{phase_name}"'
    )
)
def verify_task_stored(context, phase_name):
    """Verify the task is stored in memory with the correct EDRR phase."""
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Capture stored items for verification. ReqID: FR-40"""
        test_storage.setdefault(edrr_phase, []).append(
            {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        )
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = store_method_succeeds
    try:
        context.edrr_coordinator.start_cycle(context.task)
        phase_key = phase_name.strip('"').upper()
        assert phase_key in test_storage
        stored_items = test_storage[phase_key]
        assert any(
            item["data"] == context.task
            and item["data_type"] == MemoryType.TASK_HISTORY
            for item in stored_items
        )
        assert any("cycle_id" in item["metadata"] for item in stored_items)
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method


@then("the coordinator should store the phase transition in memory")
def verify_phase_transition_stored(context):
    """Verify the phase transition is stored in memory."""
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Capture stored items for verification. ReqID: FR-40"""
        test_storage.setdefault(edrr_phase, []).append(
            {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        )
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = store_method_succeeds
    try:
        context.edrr_coordinator.progress_to_phase(Phase.EXPAND)
        all_items = [i for items in test_storage.values() for i in items]
        assert any(item["data"] is not None for item in all_items)
        assert any(item["data_type"] == MemoryType.EPISODIC for item in all_items)
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method


@then("the WSDE team should be instructed to brainstorm approaches")
def verify_wsde_brainstorm(context):
    """Verify the WSDE team is instructed to brainstorm approaches."""
    context.edrr_coordinator._execute_expand_phase()
    assert Phase.EXPAND in context.edrr_coordinator.results
    assert "wsde_brainstorm" in context.edrr_coordinator.results[Phase.EXPAND]


@then("the WSDE team should be instructed to evaluate and compare approaches")
def verify_wsde_evaluate(context):
    """Verify the WSDE team is instructed to evaluate and compare approaches."""
    context.edrr_coordinator.results[Phase.EXPAND] = {
        "completed": True,
        "approaches": [
            {
                "id": "approach-1",
                "description": "First approach",
                "code": "def approach1(): pass",
            },
            {
                "id": "approach-2",
                "description": "Second approach",
                "code": "def approach2(): pass",
            },
        ],
    }
    context.edrr_coordinator._execute_differentiate_phase()
    assert Phase.DIFFERENTIATE in context.edrr_coordinator.results
    assert "evaluation" in context.edrr_coordinator.results[Phase.DIFFERENTIATE]


@then("the WSDE team should be instructed to implement the selected approach")
def verify_wsde_implement(context):
    """Verify the WSDE team is instructed to implement the selected approach."""
    context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
        "completed": True,
        "evaluation": {
            "selected_approach": {
                "id": "approach-1",
                "description": "Selected approach",
                "code": "def example(): pass",
            }
        },
    }
    context.edrr_coordinator._execute_refine_phase()
    assert Phase.REFINE in context.edrr_coordinator.results
    assert "implementation" in context.edrr_coordinator.results[Phase.REFINE]


@then("the WSDE team should be instructed to evaluate the implementation")
def verify_wsde_review(context):
    """Verify the WSDE team is instructed to evaluate the implementation."""
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): pass",
            "description": "Implemented solution",
        },
    }
    context.edrr_coordinator._execute_retrospect_phase()
    assert Phase.RETROSPECT in context.edrr_coordinator.results
    assert "evaluation" in context.edrr_coordinator.results[Phase.RETROSPECT]


@then("the AST analyzer should be used to analyze the file structure")
def verify_ast_analyze(context):
    """Verify the AST analyzer is used to analyze the file structure."""
    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w+", delete=False
    ) as temp_file:
        temp_file.write("def example_function():\n    return 'Hello, World!'")
        temp_file_path = temp_file.name
    try:
        context.edrr_coordinator.task = {
            "id": "task-123",
            "description": "analyze a file",
            "file_path": temp_file_path,
        }
        context.edrr_coordinator._execute_expand_phase()
        assert Phase.EXPAND in context.edrr_coordinator.results
        assert "file_analysis" in context.edrr_coordinator.results[Phase.EXPAND]
    finally:
        os.unlink(temp_file_path)


@then("the AST analyzer should be used to evaluate code quality")
def verify_ast_evaluate(context):
    """Verify the AST analyzer is used to evaluate code quality."""
    context.edrr_coordinator.task = {
        "id": "task-123",
        "description": "evaluate code",
        "code": "def example(): pass",
    }
    context.edrr_coordinator.results[Phase.EXPAND] = {
        "completed": True,
        "approaches": [
            {
                "id": "approach-1",
                "description": "First approach",
                "code": "def approach1(): pass",
            },
            {
                "id": "approach-2",
                "description": "Second approach",
                "code": "def approach2(): pass",
            },
        ],
    }
    context.edrr_coordinator._execute_differentiate_phase()
    assert Phase.DIFFERENTIATE in context.edrr_coordinator.results
    assert (
        "code_quality"
        in context.edrr_coordinator.results[Phase.DIFFERENTIATE]["evaluation"]
    )


@then("the AST analyzer should be used to apply code transformations")
def verify_ast_transform(context):
    """Verify the AST analyzer is used to apply code transformations."""
    context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
        "completed": True,
        "evaluation": {
            "selected_approach": {
                "id": "approach-1",
                "description": "Selected approach",
                "code": "def old_name(): return 'Hello, World!'",
            }
        },
    }
    context.edrr_coordinator._execute_refine_phase()
    assert Phase.REFINE in context.edrr_coordinator.results
    assert "implementation" in context.edrr_coordinator.results[Phase.REFINE]
    assert "code" in context.edrr_coordinator.results[Phase.REFINE]["implementation"]


@then("the AST analyzer should be used to verify code quality")
def verify_ast_verify(context):
    """Verify the AST analyzer is used to verify code quality."""
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): return 'Hello, World!'",
            "description": "Implemented solution",
        },
    }
    context.edrr_coordinator._execute_retrospect_phase()
    assert Phase.RETROSPECT in context.edrr_coordinator.results
    evaluation = context.edrr_coordinator.results[Phase.RETROSPECT]["evaluation"]
    assert "quality" in evaluation
    assert "is_valid" in context.edrr_coordinator.results[Phase.RETROSPECT]


@then(
    parsers.parse(
        'the prompt manager should provide templates for the "{phase_name}" phase'
    )
)
def verify_prompt_templates(context, phase_name):
    """Verify the prompt manager provides templates for the specified phase."""
    phase = Phase[phase_name.upper()]
    if phase == Phase.EXPAND:
        context.edrr_coordinator.task = {"id": "task-123", "description": "test task"}
    elif phase == Phase.DIFFERENTIATE:
        context.edrr_coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": [
                {
                    "id": "approach-1",
                    "description": "First approach",
                    "code": "def approach1(): pass",
                },
                {
                    "id": "approach-2",
                    "description": "Second approach",
                    "code": "def approach2(): pass",
                },
            ],
        }
    elif phase == Phase.REFINE:
        context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
            "completed": True,
            "evaluation": {
                "selected_approach": {
                    "id": "approach-1",
                    "description": "Selected approach",
                    "code": "def example(): pass",
                }
            },
        }
    elif phase == Phase.RETROSPECT:
        context.edrr_coordinator.results[Phase.REFINE] = {
            "completed": True,
            "implementation": {
                "code": "def example(): return 'Hello, World!'",
                "description": "Implemented solution",
            },
        }
    if phase == Phase.EXPAND:
        context.edrr_coordinator._execute_expand_phase()
    elif phase == Phase.DIFFERENTIATE:
        context.edrr_coordinator._execute_differentiate_phase()
    elif phase == Phase.REFINE:
        context.edrr_coordinator._execute_refine_phase()
    elif phase == Phase.RETROSPECT:
        context.edrr_coordinator._execute_retrospect_phase()
    assert phase in context.edrr_coordinator.results
    assert context.edrr_coordinator.results[phase] is not None


@then("the documentation manager should retrieve relevant documentation")
def verify_documentation_retrieve(context):
    """Verify the documentation manager retrieves relevant documentation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        doc_path = os.path.join(temp_dir, "sample_doc.md")
        with open(doc_path, "w") as f:
            f.write(
                "# Sample Documentation\n\nThis is a sample documentation file for testing."
            )
        context.documentation_manager.storage_path = temp_dir
        context.edrr_coordinator.task = {
            "id": "task-123",
            "description": "test task with documentation",
        }
        context.edrr_coordinator._execute_expand_phase()
        assert Phase.EXPAND in context.edrr_coordinator.results
        assert "documentation" in context.edrr_coordinator.results[Phase.EXPAND]


@then("the documentation manager should retrieve best practices documentation")
def verify_documentation_best_practices(context):
    """Verify the documentation manager retrieves best practices documentation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        doc_path = os.path.join(temp_dir, "best_practices.md")
        with open(doc_path, "w") as f:
            f.write(
                """# Best Practices

This document outlines best practices for code development."""
            )
        context.documentation_manager.storage_path = temp_dir
        context.edrr_coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": [
                {
                    "id": "approach-1",
                    "description": "First approach",
                    "code": "def approach1(): pass",
                },
                {
                    "id": "approach-2",
                    "description": "Second approach",
                    "code": "def approach2(): pass",
                },
            ],
        }
        context.edrr_coordinator._execute_differentiate_phase()
        assert Phase.DIFFERENTIATE in context.edrr_coordinator.results


@then("the documentation manager should retrieve implementation examples")
def verify_documentation_examples(context):
    """Verify the documentation manager retrieves implementation examples."""
    with tempfile.TemporaryDirectory() as temp_dir:
        doc_path = os.path.join(temp_dir, "implementation_examples.md")
        with open(doc_path, "w") as f:
            f.write(
                """# Implementation Examples

This document provides examples of implementations."""
            )
        context.documentation_manager.storage_path = temp_dir
        context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
            "completed": True,
            "evaluation": {
                "selected_approach": {
                    "id": "approach-1",
                    "description": "Selected approach",
                    "code": "def example(): pass",
                }
            },
        }
        context.edrr_coordinator._execute_refine_phase()
        assert Phase.REFINE in context.edrr_coordinator.results


@then("the documentation manager should retrieve evaluation criteria")
def verify_documentation_criteria(context):
    """Verify the documentation manager retrieves evaluation criteria."""
    with tempfile.TemporaryDirectory() as temp_dir:
        doc_path = os.path.join(temp_dir, "evaluation_criteria.md")
        with open(doc_path, "w") as f:
            f.write(
                """# Evaluation Criteria

This document outlines criteria for evaluating code quality."""
            )
        context.documentation_manager.storage_path = temp_dir
        context.edrr_coordinator.results[Phase.REFINE] = {
            "completed": True,
            "implementation": {
                "code": "def example(): return 'Hello, World!'",
                "description": "Implemented solution",
            },
        }
        context.edrr_coordinator._execute_retrospect_phase()
        assert Phase.RETROSPECT in context.edrr_coordinator.results


@then(
    parsers.parse(
        'the results should be stored in memory with EDRR phase "{phase_name}"'
    )
)
def verify_results_stored(context, phase_name):
    """Verify the results are stored in memory with the correct EDRR phase."""
    phase = Phase[phase_name.upper()]
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Test that store method succeeds.

        ReqID: N/A"""
        test_storage[edrr_phase] = {
            "data": data,
            "data_type": data_type,
            "metadata": metadata,
        }
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = store_method_succeeds
    try:
        if phase == Phase.EXPAND:
            context.edrr_coordinator.task = {
                "id": "task-123",
                "description": "test task",
            }
        elif phase == Phase.DIFFERENTIATE:
            context.edrr_coordinator.results[Phase.EXPAND] = {
                "completed": True,
                "approaches": [
                    {
                        "id": "approach-1",
                        "description": "First approach",
                        "code": "def approach1(): pass",
                    },
                    {
                        "id": "approach-2",
                        "description": "Second approach",
                        "code": "def approach2(): pass",
                    },
                ],
            }
        elif phase == Phase.REFINE:
            context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
                "completed": True,
                "evaluation": {
                    "selected_approach": {
                        "id": "approach-1",
                        "description": "Selected approach",
                        "code": "def example(): pass",
                    }
                },
            }
        elif phase == Phase.RETROSPECT:
            context.edrr_coordinator.results[Phase.REFINE] = {
                "completed": True,
                "implementation": {
                    "code": "def example(): return 'Hello, World!'",
                    "description": "Implemented solution",
                },
            }
        if phase == Phase.EXPAND:
            context.edrr_coordinator._execute_expand_phase()
        elif phase == Phase.DIFFERENTIATE:
            context.edrr_coordinator._execute_differentiate_phase()
        elif phase == Phase.REFINE:
            context.edrr_coordinator._execute_refine_phase()
        elif phase == Phase.RETROSPECT:
            context.edrr_coordinator._execute_retrospect_phase()
        assert phase_name.upper() in test_storage
        assert test_storage[phase_name.upper()]["data"] is not None
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method


@then("a final report should be generated summarizing the entire EDRR cycle")
def verify_final_report(context):
    """Verify a final report is generated."""
    context.edrr_coordinator.results = {
        Phase.EXPAND: {"completed": True, "approaches": []},
        Phase.DIFFERENTIATE: {
            "completed": True,
            "evaluation": {"selected_approach": {}},
        },
        Phase.REFINE: {"completed": True, "implementation": {}},
        Phase.RETROSPECT: {"completed": True, "evaluation": {}, "is_valid": True},
    }
    report = context.edrr_coordinator.generate_report()
    assert "task" in report
    assert "cycle_id" in report
    assert "timestamp" in report
    assert "phases" in report
    assert "summary" in report


@given("a valid EDRR manifest file exists")
def valid_manifest_file_exists(context):
    """Create a valid EDRR manifest file for testing."""
    context.temp_dir = tempfile.TemporaryDirectory()
    manifest_content = {
        "id": "test-manifest-001",
        "description": "Test manifest for EDRR coordinator",
        "metadata": {
            "version": "1.0",
            "author": "Test Author",
            "created_at": "2023-06-01T12:00:00Z",
        },
        "phases": {
            "expand": {
                "instructions": "Brainstorm approaches for the task",
                "templates": ["expand_template_1", "expand_template_2"],
                "resources": ["resource_1", "resource_2"],
                "dependencies": [],
            },
            "differentiate": {
                "instructions": "Evaluate and compare approaches",
                "templates": ["differentiate_template_1"],
                "resources": ["resource_3"],
                "dependencies": ["expand"],
            },
            "refine": {
                "instructions": "Implement the selected approach",
                "templates": ["refine_template_1"],
                "resources": ["resource_4"],
                "dependencies": ["differentiate"],
            },
            "retrospect": {
                "instructions": "Evaluate the implementation",
                "templates": ["retrospect_template_1"],
                "resources": ["resource_5"],
                "dependencies": ["refine"],
            },
        },
    }
    context.manifest_path = os.path.join(context.temp_dir.name, "test_manifest.json")
    with open(context.manifest_path, "w") as f:
        json.dump(manifest_content, f, indent=2)


@when("I start the EDRR cycle from the manifest file")
def start_edrr_cycle_from_manifest(context):
    """Start the EDRR cycle from the manifest file."""
    context.edrr_coordinator.start_cycle_from_manifest(context.manifest_path)
    if context.edrr_coordinator.current_phase == Phase.EXPAND:
        context.edrr_coordinator.execute_current_phase()


@then("the coordinator should parse the manifest successfully")
def verify_manifest_parsed(context):
    """Verify the manifest was parsed successfully."""
    assert context.edrr_coordinator.manifest_parser is not None
    assert (
        context.edrr_coordinator.manifest_parser.get_manifest_id()
        == "test-manifest-001"
    )


@then("the coordinator should use the phase instructions from the manifest")
def verify_phase_instructions_used(context):
    """Verify the phase instructions from the manifest are used."""
    expand_instructions = (
        context.edrr_coordinator.manifest_parser.get_phase_instructions(Phase.EXPAND)
    )
    assert expand_instructions == "Brainstorm approaches for the task"


@then("the coordinator should use the phase templates from the manifest")
def verify_phase_templates_used(context):
    """Verify the phase templates from the manifest are used."""
    expand_templates = context.edrr_coordinator.manifest_parser.get_phase_templates(
        Phase.EXPAND
    )
    assert "expand_template_1" in expand_templates
    assert "expand_template_2" in expand_templates


@then("the coordinator should track phase dependencies")
def verify_phase_dependencies_tracked(context):
    """Verify the phase dependencies are tracked."""
    # Dependencies for the Differentiate phase should be met once
    # the Expand phase has completed.
    assert (
        context.edrr_coordinator.manifest_parser.check_phase_dependencies(
            Phase.DIFFERENTIATE
        )
        is True
    )


@then("the coordinator should monitor execution progress")
def verify_execution_progress_monitored(context):
    """Verify the execution progress is monitored."""
    trace = context.edrr_coordinator.manifest_parser.get_execution_trace()
    assert "start_time" in trace
    assert (
        context.edrr_coordinator.manifest_parser.get_phase_status(Phase.EXPAND)
        is not None
    )


@given("the EDRR coordinator is initialized with enhanced logging")
def edrr_coordinator_with_enhanced_logging(context):
    """Initialize the EDRR coordinator with enhanced logging enabled."""
    from devsynth.application.memory.adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter,
    )

    memory_adapter = TinyDBMemoryAdapter()
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam(name="TestEdrrCoordinatorStepsTeam")
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager, storage_path="tests/fixtures/docs"
    )
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager,
        enable_enhanced_logging=True,
    )


@when(parsers.parse('I complete a full EDRR cycle with a task to "{task_description}"'))
def complete_full_edrr_cycle(context, task_description):
    """Complete a full EDRR cycle with the given task."""
    context.task = {"id": "task-123", "description": task_description}
    context.edrr_coordinator.start_cycle(context.task)

    for _ in range(10):
        phase = context.edrr_coordinator.current_phase
        if phase is None:
            break
        context.edrr_coordinator.execute_current_phase()
        if phase == Phase.RETROSPECT:
            break

    context.final_report = context.edrr_coordinator.generate_report()
    context.execution_traces = context.edrr_coordinator.get_execution_traces()


@then("the coordinator should generate detailed execution traces")
def verify_detailed_execution_traces(context):
    """Verify that the coordinator generates detailed execution traces."""
    assert context.execution_traces is not None
    assert "cycle_id" in context.execution_traces
    assert "phases" in context.execution_traces
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in context.execution_traces["phases"]


@then("the execution traces should include phase-specific metrics")
def verify_phase_specific_metrics(context):
    """Verify that the execution traces include phase-specific metrics."""
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        phase_trace = context.execution_traces["phases"][phase.name]
        assert "metrics" in phase_trace
        assert isinstance(phase_trace["metrics"], dict)


@then("the execution traces should include status tracking for each phase")
def verify_status_tracking(context):
    """Verify that the execution traces include status tracking for each phase."""
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        phase_trace = context.execution_traces["phases"][phase.name]
        assert "timestamp" in phase_trace


@then("the execution traces should include comprehensive metadata")
def verify_comprehensive_metadata(context):
    """Verify that the execution traces include comprehensive metadata."""
    assert "metadata" in context.execution_traces
    metadata = context.execution_traces["metadata"]
    assert "task_id" in metadata
    assert "task_description" in metadata
    assert "timestamp" in metadata


@then("I should be able to retrieve the full execution history")
def verify_full_execution_history(context):
    """Verify that the full execution history can be retrieved."""
    history = context.edrr_coordinator.get_execution_history()
    assert len(history) >= 4
    for entry in history:
        assert "timestamp" in entry
        assert "phase" in entry
        assert "action" in entry
        assert "details" in entry


@then("I should be able to analyze performance metrics for each phase")
def verify_performance_metrics(context):
    """Verify that performance metrics can be analyzed for each phase."""
    metrics = context.edrr_coordinator.get_performance_metrics()
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in metrics
        phase_metrics = metrics[phase.name]
        assert "duration" in phase_metrics
        assert "memory_usage" in phase_metrics
        assert "component_calls" in phase_metrics
        component_calls = phase_metrics["component_calls"]
        assert "wsde_team" in component_calls
        assert "code_analyzer" in component_calls
        assert "prompt_manager" in component_calls
        assert "documentation_manager" in component_calls
