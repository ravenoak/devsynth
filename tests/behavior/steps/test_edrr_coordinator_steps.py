"""Step definitions for the EDRR Coordinator feature."""

from pytest_bdd import given, when, then, parsers
from pytest_bdd import scenarios
import pytest

# Import the scenarios from the feature file
scenarios('../features/edrr_coordinator.feature')

# Import the necessary components

import os
import json
import tempfile
from pathlib import Path
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.edrr.manifest_parser import ManifestParser

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
    # Initialize memory adapter
    from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
    memory_adapter = TinyDBMemoryAdapter()  # Use in-memory database for testing

    # Initialize actual dependencies
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam()
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager,
        storage_path="tests/fixtures/docs"
    )

    # Initialize the actual EDRRCoordinator with actual dependencies
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager
    )


@given("the memory system is available")
def memory_system_available(context):
    """Make the memory system available."""
    # The memory manager is already initialized in edrr_coordinator_initialized
    assert context.memory_manager is not None
    assert context.edrr_coordinator.memory_manager is context.memory_manager


@given("the WSDE team is available")
def wsde_team_available(context):
    """Make the WSDE team available."""
    # The WSDE team is already initialized in edrr_coordinator_initialized
    assert context.wsde_team is not None
    assert context.edrr_coordinator.wsde_team is context.wsde_team


@given("the AST analyzer is available")
def ast_analyzer_available(context):
    """Make the AST analyzer available."""
    # The AST analyzer is already initialized in edrr_coordinator_initialized
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None
    assert context.edrr_coordinator.code_analyzer is context.code_analyzer
    assert context.edrr_coordinator.ast_transformer is context.ast_transformer


@given("the prompt manager is available")
def prompt_manager_available(context):
    """Make the prompt manager available."""
    # The prompt manager is already initialized in edrr_coordinator_initialized
    assert context.prompt_manager is not None
    assert context.edrr_coordinator.prompt_manager is context.prompt_manager


@given("the documentation manager is available")
def documentation_manager_available(context):
    """Make the documentation manager available."""
    # The documentation manager is already initialized in edrr_coordinator_initialized
    assert context.documentation_manager is not None
    assert context.edrr_coordinator.documentation_manager is context.documentation_manager


@when(parsers.parse('I start the EDRR cycle with a task to "{task_description}"'))
def start_edrr_cycle(context, task_description):
    """Start the EDRR cycle with a task."""
    context.task = {"id": "task-123", "description": task_description}
    context.edrr_coordinator.start_cycle(context.task)


@given(parsers.parse('the "{phase_name}" phase has completed for a task'))
def phase_completed(context, phase_name):
    """Set up a completed phase."""
    # Start a new cycle with a task
    context.task = {"id": "task-123", "description": "analyze a Python file"}
    context.edrr_coordinator.start_cycle(context.task)

    # Set up the phase
    phase = Phase[phase_name.upper()]

    # Create a test storage to track what's stored
    test_storage = {}

    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase

    def test_store_method(data, data_type, edrr_phase, metadata=None):
        test_storage[edrr_phase] = {
            "data": data,
            "data_type": data_type,
            "metadata": metadata
        }
        # Call the original method to maintain normal behavior
        return original_store_method(data, data_type, edrr_phase, metadata)

    # Replace the method temporarily
    context.memory_manager.store_with_edrr_phase = test_store_method

    try:
        # Set up necessary data for each phase
        if phase == Phase.EXPAND or phase == Phase.DIFFERENTIATE or phase == Phase.REFINE or phase == Phase.RETROSPECT:
            # Set up data for EXPAND phase
            context.edrr_coordinator.results[Phase.EXPAND] = {
                "completed": True,
                "approaches": [
                    {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
                    {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
                ]
            }
            context.edrr_coordinator.progress_to_phase(Phase.EXPAND)

        if phase == Phase.DIFFERENTIATE or phase == Phase.REFINE or phase == Phase.RETROSPECT:
            # Set up data for DIFFERENTIATE phase
            context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
                "completed": True,
                "evaluation": {
                    "selected_approach": {
                        "id": "approach-1",
                        "description": "Selected approach",
                        "code": "def example(): pass"
                    }
                }
            }
            context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)

        if phase == Phase.REFINE or phase == Phase.RETROSPECT:
            # Set up data for REFINE phase
            context.edrr_coordinator.results[Phase.REFINE] = {
                "completed": True,
                "implementation": {
                    "code": "def example(): return 'Hello, World!'",
                    "description": "Implemented solution"
                }
            }
            context.edrr_coordinator.progress_to_phase(Phase.REFINE)

        if phase == Phase.RETROSPECT:
            # Progress to RETROSPECT phase
            context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method

    # Ensure the phase is marked as completed
    if phase not in context.edrr_coordinator.results or not context.edrr_coordinator.results[phase].get("completed", False):
        context.edrr_coordinator.results[phase] = {
            "completed": True,
            "outputs": [{"type": "approach", "content": "Sample approach"}]
        }


@when(parsers.parse('the coordinator progresses to the "{phase_name}" phase'))
def progress_to_phase(context, phase_name):
    """Progress to the next phase."""
    context.edrr_coordinator.progress_to_phase(Phase[phase_name.upper()])


@then(parsers.parse('the coordinator should enter the "{phase_name}" phase'))
def verify_phase(context, phase_name):
    """Verify the coordinator has entered the specified phase."""
    assert context.edrr_coordinator.current_phase == Phase[phase_name.upper()]


@then("the coordinator should store the task in memory with EDRR phase {phase_name}")
def verify_task_stored(context, phase_name):
    """Verify the task is stored in memory with the correct EDRR phase."""
    # Create a test storage to track what's stored
    test_storage = {}

    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase

    def test_store_method(data, data_type, edrr_phase, metadata=None):
        test_storage[edrr_phase] = {
            "data": data,
            "data_type": data_type,
            "metadata": metadata
        }
        # Call the original method to maintain normal behavior
        return original_store_method(data, data_type, edrr_phase, metadata)

    # Replace the method temporarily
    context.memory_manager.store_with_edrr_phase = test_store_method

    try:
        # Re-execute the operation to verify it
        context.edrr_coordinator.start_cycle(context.task)

        # Verify that the task was stored with the correct phase
        phase_key = phase_name.strip('"')
        assert phase_key in test_storage
        assert test_storage[phase_key]["data"] == context.task
        assert test_storage[phase_key]["data_type"] == "TASK"
        assert "cycle_id" in test_storage[phase_key]["metadata"]
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method


@then("the coordinator should store the phase transition in memory")
def verify_phase_transition_stored(context):
    """Verify the phase transition is stored in memory."""
    # Create a test storage to track what's stored
    test_storage = {}

    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase

    def test_store_method(data, data_type, edrr_phase, metadata=None):
        test_storage[edrr_phase] = {
            "data": data,
            "data_type": data_type,
            "metadata": metadata
        }
        # Call the original method to maintain normal behavior
        return original_store_method(data, data_type, edrr_phase, metadata)

    # Replace the method temporarily
    context.memory_manager.store_with_edrr_phase = test_store_method

    try:
        # Re-execute the operation to verify it
        context.edrr_coordinator.progress_to_phase(Phase.EXPAND)

        # Verify that the phase transition was stored
        assert "EXPAND" in test_storage
        assert test_storage["EXPAND"]["data"] is not None
        assert "phase_transition" in test_storage["EXPAND"]["data_type"].lower()
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method


@then("the WSDE team should be instructed to brainstorm approaches")
def verify_wsde_brainstorm(context):
    """Verify the WSDE team is instructed to brainstorm approaches."""
    # Execute the expand phase with actual implementations
    context.edrr_coordinator._execute_expand_phase()

    # Verify that the result was stored correctly
    assert Phase.EXPAND in context.edrr_coordinator.results
    assert "wsde_brainstorm" in context.edrr_coordinator.results[Phase.EXPAND]


@then("the WSDE team should be instructed to evaluate and compare approaches")
def verify_wsde_evaluate(context):
    """Verify the WSDE team is instructed to evaluate and compare approaches."""
    # Set up the necessary data for the differentiate phase
    context.edrr_coordinator.results[Phase.EXPAND] = {
        "completed": True,
        "approaches": [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ]
    }

    # Execute the differentiate phase with actual implementation
    context.edrr_coordinator._execute_differentiate_phase()

    # Verify that the result was stored correctly
    assert Phase.DIFFERENTIATE in context.edrr_coordinator.results
    assert "evaluation" in context.edrr_coordinator.results[Phase.DIFFERENTIATE]


@then("the WSDE team should be instructed to implement the selected approach")
def verify_wsde_implement(context):
    """Verify the WSDE team is instructed to implement the selected approach."""
    # Set up the differentiate phase results
    context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
        "completed": True,
        "evaluation": {
            "selected_approach": {
                "id": "approach-1",
                "description": "Selected approach",
                "code": "def example(): pass"
            }
        }
    }

    # Execute the refine phase with actual implementation
    context.edrr_coordinator._execute_refine_phase()

    # Verify that the result was stored correctly
    assert Phase.REFINE in context.edrr_coordinator.results
    assert "implementation" in context.edrr_coordinator.results[Phase.REFINE]


@then("the WSDE team should be instructed to evaluate the implementation")
def verify_wsde_review(context):
    """Verify the WSDE team is instructed to evaluate the implementation."""
    # Set up the refine phase results
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): pass",
            "description": "Implemented solution"
        }
    }

    # Execute the retrospect phase with actual implementation
    context.edrr_coordinator._execute_retrospect_phase()

    # Verify that the result was stored correctly
    assert Phase.RETROSPECT in context.edrr_coordinator.results
    assert "evaluation" in context.edrr_coordinator.results[Phase.RETROSPECT]


@then("the AST analyzer should be used to analyze the file structure")
def verify_ast_analyze(context):
    """Verify the AST analyzer is used to analyze the file structure."""
    # Create a temporary Python file for testing
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w+', delete=False) as temp_file:
        temp_file.write("def example_function():\n    return 'Hello, World!'")
        temp_file_path = temp_file.name

    try:
        # Set up a task with the temporary file path
        context.edrr_coordinator.task = {
            "id": "task-123", 
            "description": "analyze a file", 
            "file_path": temp_file_path
        }

        # Execute the expand phase with actual implementation
        context.edrr_coordinator._execute_expand_phase()

        # Verify that the result was stored correctly
        assert Phase.EXPAND in context.edrr_coordinator.results
        assert "file_analysis" in context.edrr_coordinator.results[Phase.EXPAND]
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)


@then("the AST analyzer should be used to evaluate code quality")
def verify_ast_evaluate(context):
    """Verify the AST analyzer is used to evaluate code quality."""
    # Set up a task with code
    context.edrr_coordinator.task = {
        "id": "task-123", 
        "description": "evaluate code", 
        "code": "def example(): pass"
    }

    # Set up the expand phase results with approaches
    context.edrr_coordinator.results[Phase.EXPAND] = {
        "completed": True,
        "approaches": [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ]
    }

    # Execute the differentiate phase with actual implementation
    context.edrr_coordinator._execute_differentiate_phase()

    # Verify that the result was stored correctly
    assert Phase.DIFFERENTIATE in context.edrr_coordinator.results
    assert "code_quality" in context.edrr_coordinator.results[Phase.DIFFERENTIATE]


@then("the AST analyzer should be used to apply code transformations")
def verify_ast_transform(context):
    """Verify the AST analyzer is used to apply code transformations."""
    # Set up the differentiate phase results with code
    context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
        "completed": True,
        "evaluation": {
            "selected_approach": {
                "id": "approach-1",
                "description": "Selected approach",
                "code": "def old_name(): return 'Hello, World!'"
            }
        }
    }

    # Execute the refine phase with actual implementation
    context.edrr_coordinator._execute_refine_phase()

    # Verify that the result was stored correctly
    assert Phase.REFINE in context.edrr_coordinator.results
    assert "implementation" in context.edrr_coordinator.results[Phase.REFINE]
    assert "code" in context.edrr_coordinator.results[Phase.REFINE]["implementation"]


@then("the AST analyzer should be used to verify code quality")
def verify_ast_verify(context):
    """Verify the AST analyzer is used to verify code quality."""
    # Set up the refine phase results with code
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): return 'Hello, World!'",
            "description": "Implemented solution"
        }
    }

    # Execute the retrospect phase with actual implementation
    context.edrr_coordinator._execute_retrospect_phase()

    # Verify that the result was stored correctly
    assert Phase.RETROSPECT in context.edrr_coordinator.results
    assert "code_quality" in context.edrr_coordinator.results[Phase.RETROSPECT]
    assert "is_valid" in context.edrr_coordinator.results[Phase.RETROSPECT]


@then(parsers.parse('the prompt manager should provide templates for the "{phase_name}" phase'))
def verify_prompt_templates(context, phase_name):
    """Verify the prompt manager provides templates for the specified phase."""
    # Ensure the prompt manager has templates for the phase
    phase = Phase[phase_name.upper()]

    # Set up necessary data for the phase
    if phase == Phase.EXPAND:
        context.edrr_coordinator.task = {"id": "task-123", "description": "test task"}
    elif phase == Phase.DIFFERENTIATE:
        context.edrr_coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": [
                {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
                {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
            ]
        }
    elif phase == Phase.REFINE:
        context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
            "completed": True,
            "evaluation": {
                "selected_approach": {
                    "id": "approach-1",
                    "description": "Selected approach",
                    "code": "def example(): pass"
                }
            }
        }
    elif phase == Phase.RETROSPECT:
        context.edrr_coordinator.results[Phase.REFINE] = {
            "completed": True,
            "implementation": {
                "code": "def example(): return 'Hello, World!'",
                "description": "Implemented solution"
            }
        }

    # Execute the appropriate phase
    if phase == Phase.EXPAND:
        context.edrr_coordinator._execute_expand_phase()
    elif phase == Phase.DIFFERENTIATE:
        context.edrr_coordinator._execute_differentiate_phase()
    elif phase == Phase.REFINE:
        context.edrr_coordinator._execute_refine_phase()
    elif phase == Phase.RETROSPECT:
        context.edrr_coordinator._execute_retrospect_phase()

    # Verify that templates were used (indirectly by checking results)
    assert phase in context.edrr_coordinator.results
    assert context.edrr_coordinator.results[phase] is not None


@then("the documentation manager should retrieve relevant documentation")
def verify_documentation_retrieve(context):
    """Verify the documentation manager retrieves relevant documentation."""
    # Create a temporary directory with documentation files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample documentation file
        doc_path = os.path.join(temp_dir, "sample_doc.md")
        with open(doc_path, 'w') as f:
            f.write("# Sample Documentation\n\nThis is a sample documentation file for testing.")

        # Update the documentation manager's storage path
        context.documentation_manager.storage_path = temp_dir

        # Set up a task
        context.edrr_coordinator.task = {"id": "task-123", "description": "test task with documentation"}

        # Execute the expand phase with actual implementation
        context.edrr_coordinator._execute_expand_phase()

        # Verify that the result was stored correctly
        assert Phase.EXPAND in context.edrr_coordinator.results
        assert "documentation" in context.edrr_coordinator.results[Phase.EXPAND]


@then("the documentation manager should retrieve best practices documentation")
def verify_documentation_best_practices(context):
    """Verify the documentation manager retrieves best practices documentation."""
    # Create a temporary directory with documentation files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a best practices documentation file
        doc_path = os.path.join(temp_dir, "best_practices.md")
        with open(doc_path, 'w') as f:
            f.write("# Best Practices\n\nThis document outlines best practices for code development.")

        # Update the documentation manager's storage path
        context.documentation_manager.storage_path = temp_dir

        # Set up the expand phase results with approaches
        context.edrr_coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": [
                {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
                {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
            ]
        }

        # Execute the differentiate phase with actual implementation
        context.edrr_coordinator._execute_differentiate_phase()

        # Verify that the result was stored correctly
        assert Phase.DIFFERENTIATE in context.edrr_coordinator.results
        assert "documentation" in context.edrr_coordinator.results[Phase.DIFFERENTIATE]


@then("the documentation manager should retrieve implementation examples")
def verify_documentation_examples(context):
    """Verify the documentation manager retrieves implementation examples."""
    # Create a temporary directory with documentation files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create an implementation examples documentation file
        doc_path = os.path.join(temp_dir, "implementation_examples.md")
        with open(doc_path, 'w') as f:
            f.write("# Implementation Examples\n\nThis document provides examples of implementations.")

        # Update the documentation manager's storage path
        context.documentation_manager.storage_path = temp_dir

        # Set up the differentiate phase results
        context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
            "completed": True,
            "evaluation": {
                "selected_approach": {
                    "id": "approach-1",
                    "description": "Selected approach",
                    "code": "def example(): pass"
                }
            }
        }

        # Execute the refine phase with actual implementation
        context.edrr_coordinator._execute_refine_phase()

        # Verify that the result was stored correctly
        assert Phase.REFINE in context.edrr_coordinator.results
        assert "documentation" in context.edrr_coordinator.results[Phase.REFINE]


@then("the documentation manager should retrieve evaluation criteria")
def verify_documentation_criteria(context):
    """Verify the documentation manager retrieves evaluation criteria."""
    # Create a temporary directory with documentation files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create an evaluation criteria documentation file
        doc_path = os.path.join(temp_dir, "evaluation_criteria.md")
        with open(doc_path, 'w') as f:
            f.write("# Evaluation Criteria\n\nThis document outlines criteria for evaluating code quality.")

        # Update the documentation manager's storage path
        context.documentation_manager.storage_path = temp_dir

        # Set up the refine phase results
        context.edrr_coordinator.results[Phase.REFINE] = {
            "completed": True,
            "implementation": {
                "code": "def example(): return 'Hello, World!'",
                "description": "Implemented solution"
            }
        }

        # Execute the retrospect phase with actual implementation
        context.edrr_coordinator._execute_retrospect_phase()

        # Verify that the result was stored correctly
        assert Phase.RETROSPECT in context.edrr_coordinator.results
        assert "documentation" in context.edrr_coordinator.results[Phase.RETROSPECT]


@then(parsers.parse('the results should be stored in memory with EDRR phase "{phase_name}"'))
def verify_results_stored(context, phase_name):
    """Verify the results are stored in memory with the correct EDRR phase."""
    # Set up necessary data for the phase
    phase = Phase[phase_name.upper()]

    # Create a memory manager with a test storage
    test_storage = {}

    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase

    def test_store_method(data, data_type, edrr_phase, metadata=None):
        test_storage[edrr_phase] = {
            "data": data,
            "data_type": data_type,
            "metadata": metadata
        }
        # Call the original method to maintain normal behavior
        return original_store_method(data, data_type, edrr_phase, metadata)

    # Replace the method temporarily
    context.memory_manager.store_with_edrr_phase = test_store_method

    try:
        # Set up necessary data for the phase
        if phase == Phase.EXPAND:
            context.edrr_coordinator.task = {"id": "task-123", "description": "test task"}
        elif phase == Phase.DIFFERENTIATE:
            context.edrr_coordinator.results[Phase.EXPAND] = {
                "completed": True,
                "approaches": [
                    {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
                    {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
                ]
            }
        elif phase == Phase.REFINE:
            context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
                "completed": True,
                "evaluation": {
                    "selected_approach": {
                        "id": "approach-1",
                        "description": "Selected approach",
                        "code": "def example(): pass"
                    }
                }
            }
        elif phase == Phase.RETROSPECT:
            context.edrr_coordinator.results[Phase.REFINE] = {
                "completed": True,
                "implementation": {
                    "code": "def example(): return 'Hello, World!'",
                    "description": "Implemented solution"
                }
            }

        # Execute the appropriate phase
        if phase == Phase.EXPAND:
            context.edrr_coordinator._execute_expand_phase()
        elif phase == Phase.DIFFERENTIATE:
            context.edrr_coordinator._execute_differentiate_phase()
        elif phase == Phase.REFINE:
            context.edrr_coordinator._execute_refine_phase()
        elif phase == Phase.RETROSPECT:
            context.edrr_coordinator._execute_retrospect_phase()

        # Verify that data was stored with the correct phase
        assert phase_name.upper() in test_storage
        assert test_storage[phase_name.upper()]["data"] is not None
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method


@then("a final report should be generated summarizing the entire EDRR cycle")
def verify_final_report(context):
    """Verify a final report is generated."""
    # Set up the necessary results for all phases with actual implementation
    context.edrr_coordinator.results = {
        Phase.EXPAND: {"completed": True, "approaches": []},
        Phase.DIFFERENTIATE: {"completed": True, "evaluation": {"selected_approach": {}}},
        Phase.REFINE: {"completed": True, "implementation": {}},
        Phase.RETROSPECT: {"completed": True, "evaluation": {}, "is_valid": True}
    }

    # Generate the report
    report = context.edrr_coordinator.generate_report()

    # Verify the report contains the expected keys
    assert "task" in report
    assert "cycle_id" in report
    assert "timestamp" in report
    assert "phases" in report
    assert "summary" in report

# Step definitions for the ManifestParser integration scenario
@given("a valid EDRR manifest file exists")
def valid_manifest_file_exists(context):
    """Create a valid EDRR manifest file for testing."""
    # Create a temporary directory for test files
    context.temp_dir = tempfile.TemporaryDirectory()

    # Create a valid manifest file
    manifest_content = {
        "id": "test-manifest-001",
        "description": "Test manifest for EDRR coordinator",
        "metadata": {
            "version": "1.0",
            "author": "Test Author",
            "created_at": "2023-06-01T12:00:00Z"
        },
        "phases": {
            "expand": {
                "instructions": "Brainstorm approaches for the task",
                "templates": ["expand_template_1", "expand_template_2"],
                "resources": ["resource_1", "resource_2"],
                "dependencies": []
            },
            "differentiate": {
                "instructions": "Evaluate and compare approaches",
                "templates": ["differentiate_template_1"],
                "resources": ["resource_3"],
                "dependencies": ["expand"]
            },
            "refine": {
                "instructions": "Implement the selected approach",
                "templates": ["refine_template_1"],
                "resources": ["resource_4"],
                "dependencies": ["differentiate"]
            },
            "retrospect": {
                "instructions": "Evaluate the implementation",
                "templates": ["retrospect_template_1"],
                "resources": ["resource_5"],
                "dependencies": ["refine"]
            }
        }
    }

    # Write the manifest to a file
    context.manifest_path = os.path.join(context.temp_dir.name, "test_manifest.json")
    with open(context.manifest_path, 'w') as f:
        json.dump(manifest_content, f, indent=2)

@when("I start the EDRR cycle from the manifest file")
def start_edrr_cycle_from_manifest(context):
    """Start the EDRR cycle from the manifest file."""
    context.edrr_coordinator.start_cycle_from_manifest(context.manifest_path)

@then("the coordinator should parse the manifest successfully")
def verify_manifest_parsed(context):
    """Verify the manifest was parsed successfully."""
    # Check that the manifest parser was initialized
    assert context.edrr_coordinator._manifest_parser is not None
    # Check that the manifest ID was set correctly
    assert context.edrr_coordinator._manifest_parser.get_manifest_id() == "test-manifest-001"

@then("the coordinator should use the phase instructions from the manifest")
def verify_phase_instructions_used(context):
    """Verify the phase instructions from the manifest are used."""
    # Check that the expand phase instructions were set correctly
    expand_instructions = context.edrr_coordinator._manifest_parser.get_phase_instructions(Phase.EXPAND)
    assert expand_instructions == "Brainstorm approaches for the task"

@then("the coordinator should use the phase templates from the manifest")
def verify_phase_templates_used(context):
    """Verify the phase templates from the manifest are used."""
    # Check that the expand phase templates were set correctly
    expand_templates = context.edrr_coordinator._manifest_parser.get_phase_templates(Phase.EXPAND)
    assert "expand_template_1" in expand_templates
    assert "expand_template_2" in expand_templates

@then("the coordinator should track phase dependencies")
def verify_phase_dependencies_tracked(context):
    """Verify the phase dependencies are tracked."""
    # Check that the differentiate phase depends on expand
    assert context.edrr_coordinator._manifest_parser.check_phase_dependencies(Phase.DIFFERENTIATE) == False
    # Complete the expand phase
    context.edrr_coordinator._manifest_parser.complete_phase(Phase.EXPAND)
    # Now the differentiate phase should be ready
    assert context.edrr_coordinator._manifest_parser.check_phase_dependencies(Phase.DIFFERENTIATE) == True

@then("the coordinator should monitor execution progress")
def verify_execution_progress_monitored(context):
    """Verify the execution progress is monitored."""
    # Check that execution was started
    trace = context.edrr_coordinator._manifest_parser.get_execution_trace()
    assert "start_time" in trace
    # Check that the expand phase was started
    assert context.edrr_coordinator._manifest_parser.get_phase_status(Phase.EXPAND) is not None

# Step definitions for the comprehensive logging and traceability scenario
@given("the EDRR coordinator is initialized with enhanced logging")
def edrr_coordinator_with_enhanced_logging(context):
    """Initialize the EDRR coordinator with enhanced logging enabled."""
    # Initialize memory adapter
    from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
    memory_adapter = TinyDBMemoryAdapter()  # Use in-memory database for testing

    # Initialize actual dependencies
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam()
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager,
        storage_path="tests/fixtures/docs"
    )

    # Initialize the actual EDRRCoordinator
    # Note: Enhanced logging is simulated in the test steps rather than using a parameter
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager
    )

@when(parsers.parse('I complete a full EDRR cycle with a task to "{task_description}"'))
def complete_full_edrr_cycle(context, task_description):
    """Complete a full EDRR cycle with the given task."""
    # Start the cycle
    context.task = {"id": "task-123", "description": task_description}
    context.edrr_coordinator.start_cycle(context.task)

    # Set up necessary data for each phase and progress through all phases

    # Expand phase
    context.edrr_coordinator.results[Phase.EXPAND] = {
        "completed": True,
        "approaches": [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ]
    }
    context.edrr_coordinator.progress_to_phase(Phase.EXPAND)

    # Differentiate phase
    context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
        "completed": True,
        "evaluation": {
            "selected_approach": {
                "id": "approach-1",
                "description": "Selected approach",
                "code": "def example(): pass"
            }
        }
    }
    context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)

    # Refine phase
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): return 'Hello, World!'",
            "description": "Implemented solution"
        }
    }
    context.edrr_coordinator.progress_to_phase(Phase.REFINE)

    # Retrospect phase
    context.edrr_coordinator.results[Phase.RETROSPECT] = {
        "completed": True,
        "evaluation": {
            "quality": "good",
            "issues": [],
            "suggestions": []
        },
        "is_valid": True
    }
    context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)

    # Generate the final report
    context.final_report = context.edrr_coordinator.generate_report()

    # Get the execution traces
    context.execution_traces = context.edrr_coordinator.get_execution_traces()

@then("the coordinator should generate detailed execution traces")
def verify_detailed_execution_traces(context):
    """Verify that the coordinator generates detailed execution traces."""
    # Check that execution traces exist
    assert context.execution_traces is not None
    assert len(context.execution_traces) > 0

    # Check that the traces contain detailed information
    assert "cycle_id" in context.execution_traces
    assert "phases" in context.execution_traces
    assert "overall_status" in context.execution_traces

    # Check that each phase has traces
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in context.execution_traces["phases"]

@then("the execution traces should include phase-specific metrics")
def verify_phase_specific_metrics(context):
    """Verify that the execution traces include phase-specific metrics."""
    # Check that each phase has metrics
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        phase_trace = context.execution_traces["phases"][phase.name]
        assert "metrics" in phase_trace
        assert "duration" in phase_trace["metrics"]
        assert "memory_usage" in phase_trace["metrics"]
        assert "component_calls" in phase_trace["metrics"]

@then("the execution traces should include status tracking for each phase")
def verify_status_tracking(context):
    """Verify that the execution traces include status tracking for each phase."""
    # Check that each phase has status information
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        phase_trace = context.execution_traces["phases"][phase.name]
        assert "status" in phase_trace
        assert "start_time" in phase_trace
        assert "end_time" in phase_trace
        assert "completed" in phase_trace["status"]
        assert phase_trace["status"]["completed"] == True

@then("the execution traces should include comprehensive metadata")
def verify_comprehensive_metadata(context):
    """Verify that the execution traces include comprehensive metadata."""
    # Check that the traces contain comprehensive metadata
    assert "metadata" in context.execution_traces
    metadata = context.execution_traces["metadata"]

    # Check for various metadata fields
    assert "task_id" in metadata
    assert "task_description" in metadata
    assert "timestamp" in metadata
    assert "version" in metadata
    assert "environment" in metadata

@then("I should be able to retrieve the full execution history")
def verify_full_execution_history(context):
    """Verify that the full execution history can be retrieved."""
    # Get the full execution history
    history = context.edrr_coordinator.get_execution_history()

    # Check that the history contains entries for all phases
    assert len(history) >= 4  # At least one entry per phase

    # Check that the history entries have the expected structure
    for entry in history:
        assert "timestamp" in entry
        assert "phase" in entry
        assert "action" in entry
        assert "details" in entry

@then("I should be able to analyze performance metrics for each phase")
def verify_performance_metrics(context):
    """Verify that performance metrics can be analyzed for each phase."""
    # Get the performance metrics
    metrics = context.edrr_coordinator.get_performance_metrics()

    # Check that metrics exist for all phases
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in metrics

        # Check that each phase has the expected metrics
        phase_metrics = metrics[phase.name]
        assert "duration" in phase_metrics
        assert "memory_usage" in phase_metrics
        assert "component_calls" in phase_metrics

        # Check that component calls are tracked
        component_calls = phase_metrics["component_calls"]
        assert "wsde_team" in component_calls
        assert "code_analyzer" in component_calls
        assert "prompt_manager" in component_calls
        assert "documentation_manager" in component_calls
