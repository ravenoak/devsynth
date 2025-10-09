"""Step definitions for the Enhanced EDRR Phase Transitions feature."""

from __future__ import annotations

import json
import os
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

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
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Register feature scenarios.
scenarios(feature_path(__file__, "general", "edrr_enhanced_phase_transitions.feature"))
scenarios(feature_path(__file__, "general", "edrr_coordinator.feature"))


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
    assert context.edrr_coordinator.wsde_team is context.wsde_team


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
        """Capture stored items for verification."""
        test_storage.setdefault(edrr_phase, []).append(
            {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        )
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = test_store_method_succeeds
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
        """Capture stored items for verification."""
        test_storage.setdefault(edrr_phase, []).append(
            {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        )
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = test_store_method_succeeds
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
        """Capture stored items for verification."""
        test_storage.setdefault(edrr_phase, []).append(
            {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        )
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = test_store_method_succeeds
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
    assert (
        "code_quality"
        in context.edrr_coordinator.results[Phase.RETROSPECT]["evaluation"]
    )
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

    context.memory_manager.store_with_edrr_phase = test_store_method_succeeds
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
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): return 'Hello, World!'",
            "description": "Implemented solution",
        },
    }
    context.edrr_coordinator.progress_to_phase(Phase.REFINE)
    context.edrr_coordinator.results[Phase.RETROSPECT] = {
        "completed": True,
        "evaluation": {"quality": "good", "issues": [], "suggestions": []},
        "is_valid": True,
    }
    context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)
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


import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# noqa: F401,F403
import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
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
            self.phase_durations = {}
            self.phase_metrics = {}
            self.quality_thresholds = {}
            self.historical_data = {}
            self.context_preservation = {}

    return Context()


@given("the EDRR coordinator is initialized with enhanced phase transition features")
def edrr_coordinator_initialized_with_enhanced_features(context):
    """Initialize the EDRR coordinator with enhanced phase transition features."""
    from devsynth.application.memory.adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter,
    )

    memory_adapter = TinyDBMemoryAdapter()
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam(name="TestEdrrEnhancedPhaseTransitionsStepsTeam")
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
        config={
            "edrr": {
                "phase_transitions": {
                    "adaptive_duration": True,
                    "quality_thresholds": {
                        "expand": 0.7,
                        "differentiate": 0.7,
                        "refine": 0.8,
                        "retrospect": 0.8,
                    },
                    "use_historical_data": True,
                    "context_preservation": True,
                }
            }
        },
    )
    assert context.memory_manager is not None
    assert context.wsde_team is not None
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None
    assert context.prompt_manager is not None
    assert context.documentation_manager is not None


@given("the memory system is available")
def memory_system_available(context):
    assert context.memory_manager is not None


@given("the WSDE team is available")
def wsde_team_available(context):
    assert context.wsde_team is not None


@given("the AST analyzer is available")
def ast_analyzer_available(context):
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None


@given("the prompt manager is available")
def prompt_manager_available(context):
    assert context.prompt_manager is not None


@given("the documentation manager is available")
def documentation_manager_available(context):
    assert context.documentation_manager is not None


@given("a task with complexity score of 8 out of 10")
def task_with_high_complexity(context):
    """Create a task with high complexity."""
    context.task = {
        "id": "complex-task-123",
        "description": "Implement a distributed caching system with failover",
        "complexity_score": 8,
        "estimated_effort": "high",
    }


@when("I start the EDRR cycle with this task")
def start_edrr_cycle_with_complex_task(context):
    """Start the EDRR cycle with the complex task."""
    original_execute_expand = context.edrr_coordinator._execute_expand_phase
    original_execute_differentiate = (
        context.edrr_coordinator._execute_differentiate_phase
    )
    original_execute_refine = context.edrr_coordinator._execute_refine_phase
    original_execute_retrospect = context.edrr_coordinator._execute_retrospect_phase

    def track_duration(phase_name, original_method):

        def wrapped_method(*args, **kwargs):
            start_time = time.time()
            result = original_method(*args, **kwargs)
            end_time = time.time()
            context.phase_durations[phase_name] = end_time - start_time
            return result

        return wrapped_method

    context.edrr_coordinator._execute_expand_phase = track_duration(
        "EXPAND", original_execute_expand
    )
    context.edrr_coordinator._execute_differentiate_phase = track_duration(
        "DIFFERENTIATE", original_execute_differentiate
    )
    context.edrr_coordinator._execute_refine_phase = track_duration(
        "REFINE", original_execute_refine
    )
    context.edrr_coordinator._execute_retrospect_phase = track_duration(
        "RETROSPECT", original_execute_retrospect
    )
    context.edrr_coordinator.start_cycle(context.task)
    context.edrr_coordinator._execute_expand_phase = original_execute_expand
    context.edrr_coordinator._execute_differentiate_phase = (
        original_execute_differentiate
    )
    context.edrr_coordinator._execute_refine_phase = original_execute_refine
    context.edrr_coordinator._execute_retrospect_phase = original_execute_retrospect


@then("the coordinator should allocate more time for complex phases")
def verify_more_time_for_complex_phases(context):
    """Verify that more time is allocated for complex phases."""
    assert "EXPAND" in context.edrr_coordinator.performance_metrics
    assert "DIFFERENTIATE" in context.edrr_coordinator.performance_metrics
    assert (
        context.edrr_coordinator.performance_metrics["EXPAND"].get(
            "duration_adjustment_factor", 1.0
        )
        > 1.0
    )
    assert (
        context.edrr_coordinator.performance_metrics["DIFFERENTIATE"].get(
            "duration_adjustment_factor", 1.0
        )
        > 1.0
    )


@then('the "{phase_name}" phase should have extended duration')
def verify_phase_has_extended_duration(context, phase_name):
    """Verify that the specified phase has extended duration."""
    phase = Phase[phase_name.upper()]
    assert phase.name in context.edrr_coordinator.performance_metrics
    assert (
        "duration_adjustment_factor"
        in context.edrr_coordinator.performance_metrics[phase.name]
    )
    assert (
        context.edrr_coordinator.performance_metrics[phase.name][
            "duration_adjustment_factor"
        ]
        > 1.0
    )


@then("the phase durations should be proportional to the task complexity")
def verify_durations_proportional_to_complexity(context):
    """Verify that phase durations are proportional to task complexity."""
    complexity_score = context.task["complexity_score"]
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        if phase in context.edrr_coordinator.performance_metrics:
            adjustment_factor = context.edrr_coordinator.performance_metrics[phase].get(
                "duration_adjustment_factor", 1.0
            )
            assert abs(adjustment_factor - (1.0 + complexity_score / 10.0)) < 0.5


@then("the performance metrics should include phase duration adjustments")
def verify_metrics_include_duration_adjustments(context):
    """Verify that performance metrics include phase duration adjustments."""
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        if phase in context.edrr_coordinator.performance_metrics:
            assert (
                "duration_adjustment_factor"
                in context.edrr_coordinator.performance_metrics[phase]
            )
            assert (
                "original_duration"
                in context.edrr_coordinator.performance_metrics[phase]
            )
            assert (
                "adjusted_duration"
                in context.edrr_coordinator.performance_metrics[phase]
            )


@given("the EDRR coordinator is configured to track detailed phase metrics")
def edrr_coordinator_with_detailed_metrics(context):
    """Configure the EDRR coordinator to track detailed phase metrics."""
    context.edrr_coordinator.config["edrr"]["metrics"] = {
        "detailed_tracking": True,
        "quality_metrics": True,
        "completion_percentage": True,
        "resource_utilization": True,
        "effectiveness_score": True,
    }


@when("I complete a full EDRR cycle with a task")
def complete_full_edrr_cycle_with_metrics(context):
    """Complete a full EDRR cycle with metrics tracking."""
    context.task = {
        "id": "metrics-task-123",
        "description": "Implement a feature with metrics tracking",
    }
    context.edrr_coordinator.start_cycle(context.task)
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
        "metrics": {
            "quality_score": 0.85,
            "completion_percentage": 100,
            "resource_utilization": 0.65,
            "effectiveness_score": 0.78,
        },
    }
    context.edrr_coordinator.progress_to_phase(Phase.EXPAND)
    context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
        "completed": True,
        "evaluation": {
            "selected_approach": {
                "id": "approach-1",
                "description": "Selected approach",
                "code": "def example(): pass",
            }
        },
        "metrics": {
            "quality_score": 0.82,
            "completion_percentage": 100,
            "resource_utilization": 0.7,
            "effectiveness_score": 0.75,
        },
    }
    context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): return 'Hello, World!'",
            "description": "Implemented solution",
        },
        "metrics": {
            "quality_score": 0.88,
            "completion_percentage": 100,
            "resource_utilization": 0.75,
            "effectiveness_score": 0.82,
        },
    }
    context.edrr_coordinator.progress_to_phase(Phase.REFINE)
    context.edrr_coordinator.results[Phase.RETROSPECT] = {
        "completed": True,
        "evaluation": {"quality": "good", "issues": [], "suggestions": []},
        "is_valid": True,
        "metrics": {
            "quality_score": 0.9,
            "completion_percentage": 100,
            "resource_utilization": 0.6,
            "effectiveness_score": 0.85,
        },
    }
    context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        if phase.name in context.edrr_coordinator.results:
            context.phase_metrics[phase.name] = context.edrr_coordinator.results[
                phase.name
            ].get("metrics", {})


@then("the coordinator should generate phase-specific metrics")
def verify_phase_specific_metrics_generated(context):
    """Verify that phase-specific metrics are generated."""
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in context.phase_metrics
        assert context.phase_metrics[phase.name] is not None
        assert len(context.phase_metrics[phase.name]) > 0


@then('the metrics should include "{metric_name}" for each phase')
def verify_metric_included_for_each_phase(context, metric_name):
    """Verify that the specified metric is included for each phase."""
    metric_key = metric_name.lower().replace(" ", "_")
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in context.phase_metrics
        assert metric_key in context.phase_metrics[phase.name]
        assert context.phase_metrics[phase.name][metric_key] is not None


@then("these metrics should be stored in memory with appropriate metadata")
def verify_metrics_stored_in_memory(context):
    """Verify that metrics are stored in memory with appropriate metadata."""
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Test that store method succeeds.

        ReqID: N/A"""
        if data_type == "PHASE_METRICS":
            test_storage[edrr_phase] = {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = test_store_method
    try:
        for phase in [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]:
            if (
                phase.name in context.edrr_coordinator.results
                and "metrics" in context.edrr_coordinator.results[phase.name]
            ):
                context.memory_manager.store_with_edrr_phase(
                    context.edrr_coordinator.results[phase.name]["metrics"],
                    "PHASE_METRICS",
                    phase.name,
                    {"cycle_id": context.edrr_coordinator.cycle_id},
                )
        for phase in [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]:
            assert phase.name in test_storage
            assert test_storage[phase.name]["data_type"] == "PHASE_METRICS"
            assert "quality_score" in test_storage[phase.name]["data"]
            assert "completion_percentage" in test_storage[phase.name]["data"]
            assert "resource_utilization" in test_storage[phase.name]["data"]
            assert "effectiveness_score" in test_storage[phase.name]["data"]
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method


@given("the EDRR coordinator is configured with quality thresholds")
def edrr_coordinator_with_quality_thresholds(context):
    """Configure the EDRR coordinator with quality thresholds."""
    context.quality_thresholds = {
        "EXPAND": 0.7,
        "DIFFERENTIATE": 0.7,
        "REFINE": 0.8,
        "RETROSPECT": 0.8,
    }
    context.edrr_coordinator.config["edrr"]["phase_transitions"][
        "quality_thresholds"
    ] = {
        "expand": context.quality_thresholds["EXPAND"],
        "differentiate": context.quality_thresholds["DIFFERENTIATE"],
        "refine": context.quality_thresholds["REFINE"],
        "retrospect": context.quality_thresholds["RETROSPECT"],
    }
    original_auto_progress = context.edrr_coordinator._maybe_auto_progress

    def quality_check_auto_progress():
        phase = context.edrr_coordinator.current_phase
        if phase is None:
            return original_auto_progress()
        if phase.name in context.edrr_coordinator.results:
            phase_results = context.edrr_coordinator.results[phase.name]
            quality_score = phase_results.get("quality_score", 0.0)
            threshold = context.quality_thresholds.get(phase.name, 0.7)
            if quality_score < threshold:
                return False
        return original_auto_progress()

    context.edrr_coordinator._maybe_auto_progress = quality_check_auto_progress


@when('the "{phase_name}" phase produces results below the quality threshold')
def phase_produces_low_quality_results(context, phase_name):
    """Simulate a phase producing results below the quality threshold."""
    phase = Phase[phase_name.upper()]
    context.task = {
        "id": "quality-task-123",
        "description": "Implement a feature with quality checks",
    }
    context.edrr_coordinator.start_cycle(context.task)
    context.edrr_coordinator.results[phase] = {
        "completed": True,
        "quality_score": context.quality_thresholds[phase.name] - 0.1,
        "approaches": [
            {
                "id": "approach-1",
                "description": "Low quality approach",
                "code": "def approach1(): pass",
            }
        ],
    }
    context.edrr_coordinator.progress_to_phase(phase)
    context.edrr_coordinator._maybe_auto_progress()


@then("the coordinator should not automatically progress to the next phase")
def verify_no_auto_progression(context):
    """Verify that the coordinator does not automatically progress to the next phase."""
    assert context.edrr_coordinator.current_phase == Phase.EXPAND


@then("the coordinator should trigger additional processing in the current phase")
def verify_additional_processing_triggered(context):
    """Verify that additional processing is triggered in the current phase."""
    assert "additional_processing" in context.edrr_coordinator.results[Phase.EXPAND]
    assert (
        context.edrr_coordinator.results[Phase.EXPAND]["additional_processing"] is True
    )


@then("the coordinator should log the quality issue and remediation attempt")
def verify_quality_issue_logged(context):
    """Verify that the quality issue and remediation attempt are logged."""
    assert "quality_issues" in context.edrr_coordinator.results[Phase.EXPAND]
    assert len(context.edrr_coordinator.results[Phase.EXPAND]["quality_issues"]) > 0
    assert "remediation_attempts" in context.edrr_coordinator.results[Phase.EXPAND]
    assert (
        len(context.edrr_coordinator.results[Phase.EXPAND]["remediation_attempts"]) > 0
    )


@when("the quality threshold is met after additional processing")
def quality_threshold_met_after_processing(context):
    """Simulate the quality threshold being met after additional processing."""
    context.edrr_coordinator.results[Phase.EXPAND]["quality_score"] = (
        context.quality_thresholds["EXPAND"] + 0.1
    )
    context.edrr_coordinator._maybe_auto_progress()


@then("the coordinator should progress to the next phase")
def verify_progression_to_next_phase(context):
    """Verify that the coordinator progresses to the next phase."""
    assert context.edrr_coordinator.current_phase == Phase.DIFFERENTIATE


@then("the phase transition should include quality metrics in the metadata")
def verify_quality_metrics_in_transition_metadata(context):
    """Verify that the phase transition includes quality metrics in the metadata."""
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Test that store method succeeds.

        ReqID: N/A"""
        if data_type == "PHASE_TRANSITION":
            test_storage[edrr_phase] = {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = test_store_method
    try:
        context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        assert "DIFFERENTIATE" in test_storage
        assert test_storage["DIFFERENTIATE"]["data_type"] == "PHASE_TRANSITION"
        assert "metadata" in test_storage["DIFFERENTIATE"]
        assert "quality_metrics" in test_storage["DIFFERENTIATE"]["metadata"]
        assert (
            "quality_score"
            in test_storage["DIFFERENTIATE"]["metadata"]["quality_metrics"]
        )
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method


@given("the EDRR coordinator has completed several cycles")
def edrr_coordinator_with_completed_cycles(context):
    """Set up the EDRR coordinator with completed cycles."""
    context.historical_data = {
        "similar_task_1": {
            "cycle_id": "cycle-001",
            "task": {"id": "task-001", "description": "Similar task 1"},
            "phases": {
                "EXPAND": {
                    "duration": 10,
                    "quality_score": 0.85,
                    "strategies": ["strategy_a", "strategy_b"],
                },
                "DIFFERENTIATE": {
                    "duration": 15,
                    "quality_score": 0.82,
                    "strategies": ["strategy_c"],
                },
                "REFINE": {
                    "duration": 20,
                    "quality_score": 0.88,
                    "strategies": ["strategy_d", "strategy_e"],
                },
                "RETROSPECT": {
                    "duration": 8,
                    "quality_score": 0.9,
                    "strategies": ["strategy_f"],
                },
            },
            "success": True,
        },
        "similar_task_2": {
            "cycle_id": "cycle-002",
            "task": {"id": "task-002", "description": "Similar task 2"},
            "phases": {
                "EXPAND": {
                    "duration": 12,
                    "quality_score": 0.8,
                    "strategies": ["strategy_b", "strategy_g"],
                },
                "DIFFERENTIATE": {
                    "duration": 18,
                    "quality_score": 0.78,
                    "strategies": ["strategy_h"],
                },
                "REFINE": {
                    "duration": 25,
                    "quality_score": 0.85,
                    "strategies": ["strategy_i"],
                },
                "RETROSPECT": {
                    "duration": 10,
                    "quality_score": 0.88,
                    "strategies": ["strategy_j"],
                },
            },
            "success": True,
        },
    }
    for task_id, data in context.historical_data.items():
        context.memory_manager.store(
            data, "HISTORICAL_CYCLE_DATA", {"task_id": task_id}
        )
    original_search = context.memory_manager.search

    def search_with_historical_data(
        query=None, memory_type=None, metadata=None, limit=None
    ):
        if memory_type == "HISTORICAL_CYCLE_DATA":
            return [
                {"id": task_id, "content": data}
                for task_id, data in context.historical_data.items()
            ]
        return original_search(query, memory_type, metadata, limit)

    context.memory_manager.search = search_with_historical_data


@when("I start a new EDRR cycle with a similar task")
def start_new_cycle_with_similar_task(context):
    """Start a new EDRR cycle with a task similar to previous ones."""
    context.task = {
        "id": "similar-task-123",
        "description": "Implement a feature similar to previous tasks",
        "tags": ["similar", "feature"],
    }
    context.edrr_coordinator.start_cycle(context.task)


@then("the coordinator should use historical data to optimize phase transitions")
def verify_historical_data_used(context):
    """Verify that historical data is used to optimize phase transitions."""
    assert hasattr(context.edrr_coordinator, "_historical_data")
    assert context.edrr_coordinator._historical_data is not None
    assert len(context.edrr_coordinator._historical_data) > 0


@then(
    "the phase transition criteria should be adjusted based on previous success patterns"
)
def verify_criteria_adjusted_based_on_patterns(context):
    """Verify that phase transition criteria are adjusted based on previous success patterns."""
    assert hasattr(context.edrr_coordinator, "_adjusted_criteria")
    assert context.edrr_coordinator._adjusted_criteria is not None
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        assert phase in context.edrr_coordinator._adjusted_criteria
        assert "strategies" in context.edrr_coordinator._adjusted_criteria[phase]
        historical_strategies = set()
        for data in context.historical_data.values():
            if phase in data["phases"] and "strategies" in data["phases"][phase]:
                historical_strategies.update(data["phases"][phase]["strategies"])
        for strategy in context.edrr_coordinator._adjusted_criteria[phase][
            "strategies"
        ]:
            assert strategy in historical_strategies


@then(
    "the coordinator should prioritize strategies that were effective in similar tasks"
)
def verify_effective_strategies_prioritized(context):
    """Verify that strategies that were effective in similar tasks are prioritized."""
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        if phase in context.edrr_coordinator._adjusted_criteria:
            assert (
                "prioritized_strategies"
                in context.edrr_coordinator._adjusted_criteria[phase]
            )
            assert (
                len(
                    context.edrr_coordinator._adjusted_criteria[phase][
                        "prioritized_strategies"
                    ]
                )
                > 0
            )
            for strategy in context.edrr_coordinator._adjusted_criteria[phase][
                "prioritized_strategies"
            ]:
                found = False
                for data in context.historical_data.values():
                    if (
                        data["success"]
                        and phase in data["phases"]
                        and "strategies" in data["phases"][phase]
                    ):
                        if strategy in data["phases"][phase]["strategies"]:
                            found = True
                            break
                assert (
                    found
                ), f"Strategy {strategy} was not found in successful historical cycles"


@then("the phase transition metadata should reference the historical data used")
def verify_metadata_references_historical_data(context):
    """Verify that the phase transition metadata references the historical data used."""
    test_storage = {}
    original_store_method = context.memory_manager.store_with_edrr_phase

    def store_method_succeeds(data, data_type, edrr_phase, metadata=None):
        """Test that store method succeeds.

        ReqID: N/A"""
        if data_type == "PHASE_TRANSITION":
            test_storage[edrr_phase] = {
                "data": data,
                "data_type": data_type,
                "metadata": metadata,
            }
        return original_store_method(data, data_type, edrr_phase, metadata)

    context.memory_manager.store_with_edrr_phase = test_store_method
    try:
        context.edrr_coordinator.progress_to_phase(Phase.EXPAND)
        assert "EXPAND" in test_storage
        assert test_storage["EXPAND"]["data_type"] == "PHASE_TRANSITION"
        assert "metadata" in test_storage["EXPAND"]
        assert "historical_data_references" in test_storage["EXPAND"]["metadata"]
        assert len(test_storage["EXPAND"]["metadata"]["historical_data_references"]) > 0
        historical_cycle_ids = [
            data["cycle_id"] for data in context.historical_data.values()
        ]
        for reference in test_storage["EXPAND"]["metadata"][
            "historical_data_references"
        ]:
            assert "cycle_id" in reference
            assert reference["cycle_id"] in historical_cycle_ids
    finally:
        context.memory_manager.store_with_edrr_phase = original_store_method


@given('the EDRR coordinator is in the "{phase_name}" phase')
def edrr_coordinator_in_specific_phase(context, phase_name):
    """Set up the EDRR coordinator in a specific phase."""
    phase = Phase[phase_name.upper()]
    context.task = {
        "id": "context-task-123",
        "description": "Implement a feature with context preservation",
    }
    context.edrr_coordinator.start_cycle(context.task)
    if phase == Phase.EXPAND:
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
            "key_insights": [
                {"id": "insight-1", "description": "Important insight 1"},
                {"id": "insight-2", "description": "Important insight 2"},
            ],
            "constraints": [
                {
                    "id": "constraint-1",
                    "description": "Must be compatible with Python 3.8+",
                },
                {
                    "id": "constraint-2",
                    "description": "Must handle edge cases gracefully",
                },
            ],
        }
        context.context_preservation["key_insights"] = context.edrr_coordinator.results[
            Phase.EXPAND
        ]["key_insights"]
        context.context_preservation["constraints"] = context.edrr_coordinator.results[
            Phase.EXPAND
        ]["constraints"]
        context.context_preservation["approaches"] = context.edrr_coordinator.results[
            Phase.EXPAND
        ]["approaches"]
    context.edrr_coordinator.progress_to_phase(phase)


@when('the coordinator transitions to the "{phase_name}" phase')
def coordinator_transitions_to_phase(context, phase_name):
    """Transition the coordinator to the specified phase."""
    phase = Phase[phase_name.upper()]
    context.edrr_coordinator.progress_to_phase(phase)


@then("all relevant context from the previous phase should be preserved")
def verify_context_preserved(context):
    """Verify that all relevant context from the previous phase is preserved."""
    assert hasattr(context.edrr_coordinator, "_preserved_context")
    assert context.edrr_coordinator._preserved_context is not None
    assert "EXPAND" in context.edrr_coordinator._preserved_context
    assert context.edrr_coordinator._preserved_context["EXPAND"] is not None


@then('the context should include all key insights from the "{phase_name}" phase')
def verify_context_includes_key_insights(context, phase_name):
    """Verify that the context includes all key insights from the specified phase."""
    phase = Phase[phase_name.upper()]
    assert "key_insights" in context.edrr_coordinator._preserved_context[phase.name]
    preserved_insights = context.edrr_coordinator._preserved_context[phase.name][
        "key_insights"
    ]
    original_insights = context.context_preservation["key_insights"]
    for insight in original_insights:
        assert any(i["id"] == insight["id"] for i in preserved_insights)


@then(
    'the context should include all constraints identified in the "{phase_name}" phase'
)
def verify_context_includes_constraints(context, phase_name):
    """Verify that the context includes all constraints identified in the specified phase."""
    phase = Phase[phase_name.upper()]
    assert "constraints" in context.edrr_coordinator._preserved_context[phase.name]
    preserved_constraints = context.edrr_coordinator._preserved_context[phase.name][
        "constraints"
    ]
    original_constraints = context.context_preservation["constraints"]
    for constraint in original_constraints:
        assert any(c["id"] == constraint["id"] for c in preserved_constraints)


@then('the context should include all approaches generated in the "{phase_name}" phase')
def verify_context_includes_approaches(context, phase_name):
    """Verify that the context includes all approaches generated in the specified phase."""
    phase = Phase[phase_name.upper()]
    assert "approaches" in context.edrr_coordinator._preserved_context[phase.name]
    preserved_approaches = context.edrr_coordinator._preserved_context[phase.name][
        "approaches"
    ]
    original_approaches = context.context_preservation["approaches"]
    for approach in original_approaches:
        assert any(a["id"] == approach["id"] for a in preserved_approaches)


@then('the "{phase_name}" phase should have access to this comprehensive context')
def verify_phase_has_access_to_context(context, phase_name):
    """Verify that the specified phase has access to the comprehensive context."""
    phase = Phase[phase_name.upper()]
    assert phase.name in context.edrr_coordinator.results
    assert "context" in context.edrr_coordinator.results[phase.name]
    phase_context = context.edrr_coordinator.results[phase.name]["context"]
    assert "previous_phases" in phase_context
    assert "EXPAND" in phase_context["previous_phases"]
    previous_phase_context = phase_context["previous_phases"]["EXPAND"]
    assert "key_insights" in previous_phase_context
    assert "constraints" in previous_phase_context
    assert "approaches" in previous_phase_context
