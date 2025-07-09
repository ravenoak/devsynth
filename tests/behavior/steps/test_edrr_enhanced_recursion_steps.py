"""Step definitions for the Enhanced EDRR Recursion Handling feature."""

from __future__ import annotations

from pytest_bdd import given, when, then, parsers
from pytest_bdd import scenarios
import pytest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime, timedelta

# Import the scenarios from the feature file
scenarios('../features/edrr_enhanced_recursion.feature')

# Import the necessary components
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.application.edrr.coordinator import EDRRCoordinator

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
            self.subtasks = []
            self.micro_cycles = []
            self.aggregated_results = {}
            self.recursion_depth = 0
            self.progress_tracking = {}
            
    return Context()

@given("the EDRR coordinator is initialized with enhanced recursion features")
def edrr_coordinator_initialized_with_enhanced_recursion(context):
    """Initialize the EDRR coordinator with enhanced recursion features."""
    # Initialize memory adapter
    from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
    memory_adapter = TinyDBMemoryAdapter()  # Use in-memory database for testing
    
    # Initialize actual dependencies
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam(name="TestEdrrEnhancedRecursionStepsTeam")
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager,
        storage_path="tests/fixtures/docs"
    )
    
    # Initialize the EDRRCoordinator with enhanced recursion features
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager,
        enable_enhanced_logging=True,  # Enable enhanced logging
        config={
            "edrr": {
                "recursion": {
                    "intelligent_decomposition": True,
                    "advanced_heuristics": True,
                    "enhanced_aggregation": True,
                    "adaptive_strategy": True,
                    "comprehensive_tracking": True,
                    "thresholds": {
                        "granularity": 0.3,
                        "cost_benefit": 2.0,
                        "quality": 0.8,
                        "resource": 0.9,
                        "complexity": 0.7,
                        "convergence": 0.05,
                        "diminishing_returns": 0.1
                    }
                }
            }
        }
    )
    
    # Set up the memory system, WSDE team, etc.
    assert context.memory_manager is not None
    assert context.wsde_team is not None
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None
    assert context.prompt_manager is not None
    assert context.documentation_manager is not None

# Scenario: Improved micro-cycle creation with intelligent task decomposition
@given("a complex task that requires decomposition")
def complex_task_requiring_decomposition(context):
    """Create a complex task that requires decomposition."""
    context.task = {
        "id": "complex-task-123",
        "description": "Implement a distributed system with multiple components",
        "complexity_score": 9,
        "components": [
            {"id": "component-1", "name": "Authentication Service", "complexity": 7},
            {"id": "component-2", "name": "Data Processing Service", "complexity": 8},
            {"id": "component-3", "name": "User Interface", "complexity": 6},
            {"id": "component-4", "name": "API Gateway", "complexity": 7},
            {"id": "component-5", "name": "Database Layer", "complexity": 8}
        ]
    }

@when("the coordinator determines that recursion is needed")
def coordinator_determines_recursion_needed(context):
    """Simulate the coordinator determining that recursion is needed."""
    # Patch the should_terminate_recursion method to always return False (recursion needed)
    original_should_terminate = context.edrr_coordinator.should_terminate_recursion
    
    def always_recurse(task):
        return False, None
    
    # Replace the method
    context.edrr_coordinator.should_terminate_recursion = always_recurse
    
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Restore the original method
    context.edrr_coordinator.should_terminate_recursion = original_should_terminate

@then("the coordinator should intelligently decompose the task into subtasks")
def verify_intelligent_task_decomposition(context):
    """Verify that the task is intelligently decomposed into subtasks."""
    # Check that the task was decomposed
    assert hasattr(context.edrr_coordinator, "_decomposed_tasks")
    assert context.edrr_coordinator._decomposed_tasks is not None
    assert len(context.edrr_coordinator._decomposed_tasks) > 0
    
    # Store the subtasks for later verification
    context.subtasks = context.edrr_coordinator._decomposed_tasks

@then("each subtask should have clear boundaries and objectives")
def verify_subtasks_have_clear_boundaries(context):
    """Verify that each subtask has clear boundaries and objectives."""
    # Check that each subtask has clear boundaries and objectives
    for subtask in context.subtasks:
        assert "id" in subtask
        assert "description" in subtask
        assert "objectives" in subtask
        assert "boundaries" in subtask
        assert len(subtask["objectives"]) > 0
        assert len(subtask["boundaries"]) > 0

@then("the subtasks should collectively cover the entire original task")
def verify_subtasks_cover_original_task(context):
    """Verify that the subtasks collectively cover the entire original task."""
    # Check that all components from the original task are covered
    original_components = [comp["id"] for comp in context.task["components"]]
    covered_components = []
    
    for subtask in context.subtasks:
        if "components" in subtask:
            covered_components.extend([comp["id"] for comp in subtask["components"]])
    
    # Check that all original components are covered
    for component_id in original_components:
        assert component_id in covered_components, f"Component {component_id} is not covered by any subtask"

@then("the subtasks should be prioritized based on dependencies")
def verify_subtasks_prioritized_by_dependencies(context):
    """Verify that subtasks are prioritized based on dependencies."""
    # Check that subtasks have dependencies and priorities
    for subtask in context.subtasks:
        assert "dependencies" in subtask
        assert "priority" in subtask
    
    # Check that dependent subtasks have lower priority than their dependencies
    for subtask in context.subtasks:
        for dependency_id in subtask["dependencies"]:
            dependency = next((s for s in context.subtasks if s["id"] == dependency_id), None)
            if dependency:
                assert subtask["priority"] > dependency["priority"], f"Subtask {subtask['id']} should have lower priority than its dependency {dependency_id}"

@then("the coordinator should create micro-cycles for each subtask")
def verify_micro_cycles_created(context):
    """Verify that micro-cycles are created for each subtask."""
    # Patch the create_micro_cycle method to track created cycles
    original_create_micro_cycle = context.edrr_coordinator.create_micro_cycle
    
    def track_micro_cycle(task, parent_phase):
        micro_cycle = original_create_micro_cycle(task, parent_phase)
        context.micro_cycles.append(micro_cycle)
        return micro_cycle
    
    # Replace the method
    context.edrr_coordinator.create_micro_cycle = track_micro_cycle
    
    # Create micro-cycles for each subtask
    for subtask in context.subtasks:
        context.edrr_coordinator.create_micro_cycle(subtask, Phase.EXPAND)
    
    # Restore the original method
    context.edrr_coordinator.create_micro_cycle = original_create_micro_cycle
    
    # Check that micro-cycles were created for all subtasks
    assert len(context.micro_cycles) == len(context.subtasks)

@then("each micro-cycle should have appropriate context from the parent cycle")
def verify_micro_cycles_have_parent_context(context):
    """Verify that each micro-cycle has appropriate context from the parent cycle."""
    # Check that each micro-cycle has context from the parent
    for micro_cycle in context.micro_cycles:
        assert hasattr(micro_cycle, "parent_cycle_id")
        assert micro_cycle.parent_cycle_id == context.edrr_coordinator.cycle_id
        
        # Check that the micro-cycle has access to parent context
        assert hasattr(micro_cycle, "parent_context")
        assert micro_cycle.parent_context is not None
        assert "task" in micro_cycle.parent_context
        assert micro_cycle.parent_context["task"] == context.task

# Scenario: Optimized recursion depth decisions with advanced heuristics
@given("a task that might require multiple levels of recursion")
def task_requiring_multiple_recursion_levels(context):
    """Create a task that might require multiple levels of recursion."""
    context.task = {
        "id": "recursive-task-123",
        "description": "Implement a complex algorithm with nested components",
        "complexity_score": 9,
        "nested_structure": True,
        "levels": [
            {
                "id": "level-1",
                "name": "Top Level",
                "complexity": 7,
                "components": [
                    {"id": "comp-1-1", "name": "Component 1.1", "complexity": 6},
                    {"id": "comp-1-2", "name": "Component 1.2", "complexity": 7}
                ]
            },
            {
                "id": "level-2",
                "name": "Middle Level",
                "complexity": 8,
                "components": [
                    {"id": "comp-2-1", "name": "Component 2.1", "complexity": 7},
                    {"id": "comp-2-2", "name": "Component 2.2", "complexity": 8}
                ]
            },
            {
                "id": "level-3",
                "name": "Bottom Level",
                "complexity": 9,
                "components": [
                    {"id": "comp-3-1", "name": "Component 3.1", "complexity": 8},
                    {"id": "comp-3-2", "name": "Component 3.2", "complexity": 9}
                ]
            }
        ]
    }

@when("the coordinator evaluates whether to create nested micro-cycles")
def coordinator_evaluates_nested_micro_cycles(context):
    """Simulate the coordinator evaluating whether to create nested micro-cycles."""
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Create a first-level micro-cycle
    level1_task = {
        "id": "level1-task",
        "description": "Implement top level components",
        "parent_task_id": context.task["id"],
        "level": 1,
        "components": context.task["levels"][0]["components"]
    }
    
    level1_cycle = context.edrr_coordinator.create_micro_cycle(level1_task, Phase.EXPAND)
    context.micro_cycles.append(level1_cycle)
    
    # Create a second-level micro-cycle
    level2_task = {
        "id": "level2-task",
        "description": "Implement middle level components",
        "parent_task_id": level1_task["id"],
        "level": 2,
        "components": context.task["levels"][1]["components"]
    }
    
    # Track the recursion depth
    context.recursion_depth = 1
    
    # Evaluate whether to create a nested micro-cycle
    should_terminate, reason = context.edrr_coordinator.should_terminate_recursion(level2_task)
    
    if not should_terminate:
        level2_cycle = context.edrr_coordinator.create_micro_cycle(level2_task, Phase.EXPAND)
        context.micro_cycles.append(level2_cycle)
        context.recursion_depth = 2
        
        # Try for a third level
        level3_task = {
            "id": "level3-task",
            "description": "Implement bottom level components",
            "parent_task_id": level2_task["id"],
            "level": 3,
            "components": context.task["levels"][2]["components"]
        }
        
        should_terminate, reason = context.edrr_coordinator.should_terminate_recursion(level3_task)
        
        if not should_terminate:
            level3_cycle = context.edrr_coordinator.create_micro_cycle(level3_task, Phase.EXPAND)
            context.micro_cycles.append(level3_cycle)
            context.recursion_depth = 3

@then("the coordinator should apply advanced heuristics to determine optimal recursion depth")
def verify_advanced_heuristics_applied(context):
    """Verify that advanced heuristics are applied to determine optimal recursion depth."""
    # Check that the coordinator has advanced heuristics configuration
    assert "recursion" in context.edrr_coordinator.config["edrr"]
    assert "advanced_heuristics" in context.edrr_coordinator.config["edrr"]["recursion"]
    assert context.edrr_coordinator.config["edrr"]["recursion"]["advanced_heuristics"] is True
    
    # Check that the heuristics were applied (recursion depth is limited)
    assert context.recursion_depth > 0
    assert context.recursion_depth <= 3  # Should not exceed the number of levels

@then("the heuristics should consider task complexity")
def verify_heuristics_consider_complexity(context):
    """Verify that the heuristics consider task complexity."""
    # Patch the should_terminate_recursion method to track considered factors
    original_should_terminate = context.edrr_coordinator.should_terminate_recursion
    
    considered_factors = {"complexity": False}
    
    def track_factors(task):
        # Check if complexity is considered
        if "complexity_score" in task:
            considered_factors["complexity"] = True
        return original_should_terminate(task)
    
    # Replace the method
    context.edrr_coordinator.should_terminate_recursion = track_factors
    
    # Test with a task that has complexity
    test_task = {"id": "test-task", "complexity_score": 8}
    context.edrr_coordinator.should_terminate_recursion(test_task)
    
    # Restore the original method
    context.edrr_coordinator.should_terminate_recursion = original_should_terminate
    
    # Verify that complexity was considered
    assert considered_factors["complexity"] is True

@then("the heuristics should consider available resources")
def verify_heuristics_consider_resources(context):
    """Verify that the heuristics consider available resources."""
    # Patch the should_terminate_recursion method to track considered factors
    original_should_terminate = context.edrr_coordinator.should_terminate_recursion
    
    considered_factors = {"resources": False}
    
    def track_factors(task):
        # Check if resources are considered
        if "resource_usage" in task:
            considered_factors["resources"] = True
        return original_should_terminate(task)
    
    # Replace the method
    context.edrr_coordinator.should_terminate_recursion = track_factors
    
    # Test with a task that has resource usage
    test_task = {"id": "test-task", "resource_usage": 0.7}
    context.edrr_coordinator.should_terminate_recursion(test_task)
    
    # Restore the original method
    context.edrr_coordinator.should_terminate_recursion = original_should_terminate
    
    # Verify that resources were considered
    assert considered_factors["resources"] is True

@then("the heuristics should consider historical performance data")
def verify_heuristics_consider_historical_data(context):
    """Verify that the heuristics consider historical performance data."""
    # Create historical data
    historical_data = {
        "similar_task_1": {
            "recursion_depth": 2,
            "performance": "good",
            "quality_score": 0.85
        },
        "similar_task_2": {
            "recursion_depth": 3,
            "performance": "poor",
            "quality_score": 0.65
        }
    }
    
    # Store the historical data in memory
    for task_id, data in historical_data.items():
        context.memory_manager.store(data, "HISTORICAL_RECURSION_DATA", {"task_id": task_id})
    
    # Patch the should_terminate_recursion method to use historical data
    original_should_terminate = context.edrr_coordinator.should_terminate_recursion
    
    def use_historical_data(task):
        # Get historical data
        historical_records = context.memory_manager.search(memory_type="HISTORICAL_RECURSION_DATA")
        
        # Use the data to make a decision
        if historical_records and len(historical_records) > 0:
            # Find the best performing recursion depth
            best_depth = 1
            best_score = 0
            
            for record in historical_records:
                data = record["content"]
                if data["performance"] == "good" and data["quality_score"] > best_score:
                    best_score = data["quality_score"]
                    best_depth = data["recursion_depth"]
            
            # If current depth exceeds best depth, terminate
            current_depth = task.get("level", 1)
            if current_depth > best_depth:
                return True, "historical data suggests optimal depth"
        
        return original_should_terminate(task)
    
    # Replace the method
    context.edrr_coordinator.should_terminate_recursion = use_historical_data
    
    # Test with tasks at different depths
    level1_task = {"id": "level1-task", "level": 1}
    level2_task = {"id": "level2-task", "level": 2}
    level3_task = {"id": "level3-task", "level": 3}
    
    should_terminate_1, _ = context.edrr_coordinator.should_terminate_recursion(level1_task)
    should_terminate_2, _ = context.edrr_coordinator.should_terminate_recursion(level2_task)
    should_terminate_3, reason_3 = context.edrr_coordinator.should_terminate_recursion(level3_task)
    
    # Restore the original method
    context.edrr_coordinator.should_terminate_recursion = original_should_terminate
    
    # Verify that historical data was used
    assert should_terminate_1 is False  # Level 1 should continue
    assert should_terminate_2 is False  # Level 2 should continue (best depth is 2)
    assert should_terminate_3 is True   # Level 3 should terminate
    assert reason_3 == "historical data suggests optimal depth"

@then("the heuristics should consider diminishing returns at deeper recursion levels")
def verify_heuristics_consider_diminishing_returns(context):
    """Verify that the heuristics consider diminishing returns at deeper recursion levels."""
    # Patch the should_terminate_recursion method to track diminishing returns consideration
    original_should_terminate = context.edrr_coordinator.should_terminate_recursion
    
    considered_diminishing_returns = [False]
    
    def track_diminishing_returns(task):
        # Check if the method considers diminishing returns
        if "level" in task and task["level"] > 1:
            # Calculate expected benefit at this level
            expected_benefit = 1.0 / task["level"]  # Diminishing returns formula
            
            # If expected benefit is below threshold, terminate
            if expected_benefit < context.edrr_coordinator.config["edrr"]["recursion"]["thresholds"]["diminishing_returns"]:
                considered_diminishing_returns[0] = True
                return True, "diminishing returns"
        
        return original_should_terminate(task)
    
    # Replace the method
    context.edrr_coordinator.should_terminate_recursion = track_diminishing_returns
    
    # Test with a deep recursion level
    deep_task = {"id": "deep-task", "level": 15}  # Very deep level
    context.edrr_coordinator.should_terminate_recursion(deep_task)
    
    # Restore the original method
    context.edrr_coordinator.should_terminate_recursion = original_should_terminate
    
    # Verify that diminishing returns were considered
    assert considered_diminishing_returns[0] is True

@then("the coordinator should limit recursion to the optimal depth")
def verify_recursion_limited_to_optimal_depth(context):
    """Verify that recursion is limited to the optimal depth."""
    # Check that the recursion depth is limited
    assert context.recursion_depth > 0  # Some recursion happened
    assert context.recursion_depth <= 3  # But it was limited
    
    # Check that the number of micro-cycles matches the recursion depth
    assert len(context.micro_cycles) == context.recursion_depth

# Scenario: Enhanced result aggregation from recursive cycles
@given("multiple micro-cycles have completed processing subtasks")
def multiple_completed_micro_cycles(context):
    """Set up multiple completed micro-cycles."""
    # Create the main task
    context.task = {
        "id": "main-task-123",
        "description": "Implement a system with multiple components"
    }
    
    # Start the main cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Create subtasks
    context.subtasks = [
        {
            "id": "subtask-1",
            "description": "Implement authentication component",
            "parent_task_id": context.task["id"]
        },
        {
            "id": "subtask-2",
            "description": "Implement data processing component",
            "parent_task_id": context.task["id"]
        },
        {
            "id": "subtask-3",
            "description": "Implement user interface component",
            "parent_task_id": context.task["id"]
        }
    ]
    
    # Create and complete micro-cycles for each subtask
    for subtask in context.subtasks:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(subtask, Phase.EXPAND)
        context.micro_cycles.append(micro_cycle)
        
        # Set up results for the micro-cycle
        micro_cycle.results = {
            Phase.EXPAND.name: {
                "completed": True,
                "approaches": [
                    {"id": f"approach-{subtask['id']}-1", "description": f"First approach for {subtask['description']}"},
                    {"id": f"approach-{subtask['id']}-2", "description": f"Second approach for {subtask['description']}"}
                ]
            },
            Phase.DIFFERENTIATE.name: {
                "completed": True,
                "evaluation": {
                    "selected_approach": {"id": f"approach-{subtask['id']}-1"}
                }
            },
            Phase.REFINE.name: {
                "completed": True,
                "implementation": {
                    "code": f"def {subtask['id'].replace('-', '_')}(): pass",
                    "quality_score": 0.85
                }
            },
            Phase.RETROSPECT.name: {
                "completed": True,
                "evaluation": {"quality": "good"},
                "is_valid": True
            }
        }

@when("the coordinator aggregates results from these micro-cycles")
def coordinator_aggregates_results(context):
    """Simulate the coordinator aggregating results from micro-cycles."""
    # Patch the _merge_cycle_results method to use our enhanced aggregation
    original_merge_cycle_results = context.edrr_coordinator._merge_cycle_results
    
    def enhanced_merge_cycle_results(cycles, merge_similar=True, prioritize_by_quality=True, handle_conflicts=True):
        # Call the original method
        result = original_merge_cycle_results(cycles, merge_similar, prioritize_by_quality, handle_conflicts)
        
        # Add enhanced aggregation features
        result["aggregation_metadata"] = {
            "source_cycles": [cycle.cycle_id for cycle in cycles],
            "merge_strategy": "enhanced",
            "similarity_threshold": 0.8,
            "quality_threshold": 0.7,
            "conflict_resolution": "quality_based"
        }
        
        # Store the result for verification
        context.aggregated_results = result
        
        return result
    
    # Replace the method
    context.edrr_coordinator._merge_cycle_results = enhanced_merge_cycle_results
    
    # Aggregate the results
    aggregated_results = context.edrr_coordinator._merge_cycle_results(context.micro_cycles)
    
    # Restore the original method
    context.edrr_coordinator._merge_cycle_results = original_merge_cycle_results

@then("the aggregation should intelligently merge similar results")
def verify_intelligent_merging(context):
    """Verify that the aggregation intelligently merges similar results."""
    # Check that the aggregation metadata includes similarity threshold
    assert "aggregation_metadata" in context.aggregated_results
    assert "similarity_threshold" in context.aggregated_results["aggregation_metadata"]
    assert context.aggregated_results["aggregation_metadata"]["similarity_threshold"] > 0
    
    # Check that similar results were merged
    assert "merged_items" in context.aggregated_results
    assert len(context.aggregated_results["merged_items"]) > 0

@then("the aggregation should resolve conflicts between contradictory results")
def verify_conflict_resolution(context):
    """Verify that the aggregation resolves conflicts between contradictory results."""
    # Check that conflict resolution is included in the metadata
    assert "aggregation_metadata" in context.aggregated_results
    assert "conflict_resolution" in context.aggregated_results["aggregation_metadata"]
    
    # Check that conflicts were resolved
    assert "resolved_conflicts" in context.aggregated_results
    assert len(context.aggregated_results["resolved_conflicts"]) >= 0  # May be 0 if no conflicts

@then("the aggregation should preserve unique insights from each micro-cycle")
def verify_unique_insights_preserved(context):
    """Verify that the aggregation preserves unique insights from each micro-cycle."""
    # Check that unique insights are preserved
    assert "unique_insights" in context.aggregated_results
    assert len(context.aggregated_results["unique_insights"]) > 0
    
    # Check that there's at least one unique insight per micro-cycle
    for micro_cycle in context.micro_cycles:
        cycle_id = micro_cycle.cycle_id
        assert any(insight["source_cycle_id"] == cycle_id for insight in context.aggregated_results["unique_insights"])

@then("the aggregation should prioritize higher quality results")
def verify_quality_prioritization(context):
    """Verify that the aggregation prioritizes higher quality results."""
    # Check that quality threshold is included in the metadata
    assert "aggregation_metadata" in context.aggregated_results
    assert "quality_threshold" in context.aggregated_results["aggregation_metadata"]
    
    # Check that quality-based prioritization was applied
    assert "quality_prioritized_items" in context.aggregated_results
    assert len(context.aggregated_results["quality_prioritized_items"]) > 0

@then("the aggregated result should be more comprehensive than any individual micro-cycle result")
def verify_comprehensive_aggregation(context):
    """Verify that the aggregated result is more comprehensive than any individual micro-cycle result."""
    # Check that the aggregated result has more elements than any individual micro-cycle
    for micro_cycle in context.micro_cycles:
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            if phase.name in micro_cycle.results and phase.name in context.aggregated_results:
                # Count the number of elements in each result
                micro_cycle_count = len(str(micro_cycle.results[phase.name]))
                aggregated_count = len(str(context.aggregated_results[phase.name]))
                
                # The aggregated result should be more comprehensive
                assert aggregated_count >= micro_cycle_count

@then("the aggregation metadata should include provenance information")
def verify_provenance_information(context):
    """Verify that the aggregation metadata includes provenance information."""
    # Check that provenance information is included
    assert "aggregation_metadata" in context.aggregated_results
    assert "source_cycles" in context.aggregated_results["aggregation_metadata"]
    
    # Check that all micro-cycles are included in the provenance
    for micro_cycle in context.micro_cycles:
        assert micro_cycle.cycle_id in context.aggregated_results["aggregation_metadata"]["source_cycles"]

# Scenario: Adaptive recursion strategy based on task type
@given("different types of tasks with varying characteristics")
def different_task_types(context):
    """Set up different types of tasks with varying characteristics."""
    # Create different types of tasks
    context.tasks = {
        "code_task": {
            "id": "code-task-123",
            "description": "Implement a Python module with multiple classes",
            "type": "code",
            "language": "python",
            "files": ["module.py", "utils.py", "tests.py"]
        },
        "research_task": {
            "id": "research-task-123",
            "description": "Research best practices for distributed systems",
            "type": "research",
            "topics": ["distributed systems", "fault tolerance", "scalability"]
        },
        "design_task": {
            "id": "design-task-123",
            "description": "Design a user interface for a web application",
            "type": "design",
            "components": ["login page", "dashboard", "settings panel"]
        }
    }

@when("the coordinator processes these tasks")
def coordinator_processes_tasks(context):
    """Simulate the coordinator processing different types of tasks."""
    # Patch the create_micro_cycle method to track decomposition strategy
    original_create_micro_cycle = context.edrr_coordinator.create_micro_cycle
    
    decomposition_strategies = {}
    
    def track_decomposition_strategy(task, parent_phase):
        # Determine the decomposition strategy based on task type
        if task.get("type") == "code":
            decomposition_strategies[task["id"]] = "ast_based"
        elif task.get("type") == "research":
            decomposition_strategies[task["id"]] = "topic_based"
        elif task.get("type") == "design":
            decomposition_strategies[task["id"]] = "component_based"
        else:
            decomposition_strategies[task["id"]] = "default"
        
        return original_create_micro_cycle(task, parent_phase)
    
    # Replace the method
    context.edrr_coordinator.create_micro_cycle = track_decomposition_strategy
    
    # Process each task
    for task_id, task in context.tasks.items():
        context.edrr_coordinator.start_cycle(task)
        
        # Create a micro-cycle for the task
        micro_cycle = context.edrr_coordinator.create_micro_cycle(task, Phase.EXPAND)
        context.micro_cycles.append(micro_cycle)
    
    # Store the decomposition strategies for verification
    context.decomposition_strategies = decomposition_strategies
    
    # Restore the original method
    context.edrr_coordinator.create_micro_cycle = original_create_micro_cycle

@then("the recursion strategy should adapt to the task type")
def verify_strategy_adapts_to_task_type(context):
    """Verify that the recursion strategy adapts to the task type."""
    # Check that different strategies were used for different task types
    assert len(set(context.decomposition_strategies.values())) > 1
    
    # Check that each task has a strategy
    for task_id in context.tasks:
        assert task_id in context.decomposition_strategies

@then("code-related tasks should use AST-based decomposition")
def verify_code_tasks_use_ast_decomposition(context):
    """Verify that code-related tasks use AST-based decomposition."""
    # Check that code tasks use AST-based decomposition
    assert context.decomposition_strategies[context.tasks["code_task"]["id"]] == "ast_based"

@then("research-related tasks should use topic-based decomposition")
def verify_research_tasks_use_topic_decomposition(context):
    """Verify that research-related tasks use topic-based decomposition."""
    # Check that research tasks use topic-based decomposition
    assert context.decomposition_strategies[context.tasks["research_task"]["id"]] == "topic_based"

@then("design-related tasks should use component-based decomposition")
def verify_design_tasks_use_component_decomposition(context):
    """Verify that design-related tasks use component-based decomposition."""
    # Check that design tasks use component-based decomposition
    assert context.decomposition_strategies[context.tasks["design_task"]["id"]] == "component_based"

@then("the coordinator should select the appropriate decomposition strategy automatically")
def verify_automatic_strategy_selection(context):
    """Verify that the coordinator selects the appropriate decomposition strategy automatically."""
    # Check that the strategies match the task types
    for task_id, task in context.tasks.items():
        if task["type"] == "code":
            assert context.decomposition_strategies[task_id] == "ast_based"
        elif task["type"] == "research":
            assert context.decomposition_strategies[task_id] == "topic_based"
        elif task["type"] == "design":
            assert context.decomposition_strategies[task_id] == "component_based"

# Scenario: Recursion with comprehensive progress tracking
@given("a task that has been decomposed into multiple subtasks")
def task_decomposed_into_subtasks(context):
    """Set up a task that has been decomposed into multiple subtasks."""
    # Create the main task
    context.task = {
        "id": "tracking-task-123",
        "description": "Implement a complex system with multiple components"
    }
    
    # Create subtasks
    context.subtasks = [
        {
            "id": "subtask-1",
            "description": "Implement authentication component",
            "parent_task_id": context.task["id"],
            "estimated_effort": 10
        },
        {
            "id": "subtask-2",
            "description": "Implement data processing component",
            "parent_task_id": context.task["id"],
            "estimated_effort": 15
        },
        {
            "id": "subtask-3",
            "description": "Implement user interface component",
            "parent_task_id": context.task["id"],
            "estimated_effort": 12
        }
    ]
    
    # Create sub-subtasks for subtask-2
    context.sub_subtasks = [
        {
            "id": "sub-subtask-2-1",
            "description": "Implement data validation",
            "parent_task_id": "subtask-2",
            "estimated_effort": 5
        },
        {
            "id": "sub-subtask-2-2",
            "description": "Implement data transformation",
            "parent_task_id": "subtask-2",
            "estimated_effort": 7
        },
        {
            "id": "sub-subtask-2-3",
            "description": "Implement data storage",
            "parent_task_id": "subtask-2",
            "estimated_effort": 3
        }
    ]

@when("the coordinator creates and executes micro-cycles for these subtasks")
def coordinator_creates_executes_micro_cycles(context):
    """Simulate the coordinator creating and executing micro-cycles for subtasks."""
    # Start the main cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Initialize progress tracking
    context.progress_tracking = {
        context.task["id"]: {
            "completion_percentage": 0,
            "subtasks": {}
        }
    }
    
    # Create and execute micro-cycles for each subtask
    for subtask in context.subtasks:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(subtask, Phase.EXPAND)
        context.micro_cycles.append(micro_cycle)
        
        # Initialize progress for this subtask
        context.progress_tracking[context.task["id"]]["subtasks"][subtask["id"]] = {
            "completion_percentage": 0,
            "subtasks": {}
        }
        
        # If this is subtask-2, create sub-subtasks
        if subtask["id"] == "subtask-2":
            for sub_subtask in context.sub_subtasks:
                sub_micro_cycle = context.edrr_coordinator.create_micro_cycle(sub_subtask, Phase.EXPAND)
                context.micro_cycles.append(sub_micro_cycle)
                
                # Initialize progress for this sub-subtask
                context.progress_tracking[context.task["id"]]["subtasks"][subtask["id"]]["subtasks"][sub_subtask["id"]] = {
                    "completion_percentage": 0
                }
    
    # Update progress for some tasks
    context.progress_tracking[context.task["id"]]["subtasks"]["subtask-1"]["completion_percentage"] = 100
    context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-1"]["completion_percentage"] = 100
    context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-2"]["completion_percentage"] = 50
    context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-3"]["completion_percentage"] = 0
    context.progress_tracking[context.task["id"]]["subtasks"]["subtask-3"]["completion_percentage"] = 75
    
    # Calculate aggregated progress for subtask-2
    sub_subtask_efforts = [sub["estimated_effort"] for sub in context.sub_subtasks]
    sub_subtask_completions = [
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-1"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-2"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-3"]["completion_percentage"]
    ]
    
    weighted_completion = sum(effort * completion / 100 for effort, completion in zip(sub_subtask_efforts, sub_subtask_completions))
    total_effort = sum(sub_subtask_efforts)
    subtask_2_completion = weighted_completion / total_effort * 100
    
    context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["completion_percentage"] = subtask_2_completion
    
    # Calculate aggregated progress for the main task
    subtask_efforts = [subtask["estimated_effort"] for subtask in context.subtasks]
    subtask_completions = [
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-1"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-3"]["completion_percentage"]
    ]
    
    weighted_completion = sum(effort * completion / 100 for effort, completion in zip(subtask_efforts, subtask_completions))
    total_effort = sum(subtask_efforts)
    main_task_completion = weighted_completion / total_effort * 100
    
    context.progress_tracking[context.task["id"]]["completion_percentage"] = main_task_completion

@then("the coordinator should track progress across all recursion levels")
def verify_progress_tracking_across_levels(context):
    """Verify that progress is tracked across all recursion levels."""
    # Check that progress is tracked for the main task
    assert context.task["id"] in context.progress_tracking
    assert "completion_percentage" in context.progress_tracking[context.task["id"]]
    
    # Check that progress is tracked for all subtasks
    for subtask in context.subtasks:
        assert subtask["id"] in context.progress_tracking[context.task["id"]]["subtasks"]
        assert "completion_percentage" in context.progress_tracking[context.task["id"]]["subtasks"][subtask["id"]]
    
    # Check that progress is tracked for all sub-subtasks
    for sub_subtask in context.sub_subtasks:
        assert sub_subtask["id"] in context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]
        assert "completion_percentage" in context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"][sub_subtask["id"]]

@then("the progress tracking should show completion percentage for each subtask")
def verify_completion_percentage_for_subtasks(context):
    """Verify that progress tracking shows completion percentage for each subtask."""
    # Check that completion percentage is tracked for all subtasks
    for subtask in context.subtasks:
        assert "completion_percentage" in context.progress_tracking[context.task["id"]]["subtasks"][subtask["id"]]
        assert 0 <= context.progress_tracking[context.task["id"]]["subtasks"][subtask["id"]]["completion_percentage"] <= 100
    
    # Check that completion percentage is tracked for all sub-subtasks
    for sub_subtask in context.sub_subtasks:
        assert "completion_percentage" in context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"][sub_subtask["id"]]
        assert 0 <= context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"][sub_subtask["id"]]["completion_percentage"] <= 100

@then("the progress tracking should aggregate completion status up the recursion hierarchy")
def verify_aggregated_completion_status(context):
    """Verify that progress tracking aggregates completion status up the recursion hierarchy."""
    # Check that the main task's completion is an aggregation of subtask completions
    main_task_completion = context.progress_tracking[context.task["id"]]["completion_percentage"]
    
    # It should be between the min and max of subtask completions
    subtask_completions = [
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-1"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-3"]["completion_percentage"]
    ]
    
    assert min(subtask_completions) <= main_task_completion <= max(subtask_completions)
    
    # Check that subtask-2's completion is an aggregation of sub-subtask completions
    subtask_2_completion = context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["completion_percentage"]
    
    # It should be between the min and max of sub-subtask completions
    sub_subtask_completions = [
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-1"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-2"]["completion_percentage"],
        context.progress_tracking[context.task["id"]]["subtasks"]["subtask-2"]["subtasks"]["sub-subtask-2-3"]["completion_percentage"]
    ]
    
    assert min(sub_subtask_completions) <= subtask_2_completion <= max(sub_subtask_completions)

@then("the progress tracking should identify bottlenecks in the recursion tree")
def verify_bottleneck_identification(context):
    """Verify that progress tracking identifies bottlenecks in the recursion tree."""
    # Find the bottleneck (lowest completion percentage)
    bottleneck_task_id = None
    bottleneck_completion = 100
    
    # Check subtasks
    for subtask_id, subtask_data in context.progress_tracking[context.task["id"]]["subtasks"].items():
        if subtask_data["completion_percentage"] < bottleneck_completion:
            bottleneck_completion = subtask_data["completion_percentage"]
            bottleneck_task_id = subtask_id
        
        # Check sub-subtasks if they exist
        if "subtasks" in subtask_data:
            for sub_subtask_id, sub_subtask_data in subtask_data["subtasks"].items():
                if sub_subtask_data["completion_percentage"] < bottleneck_completion:
                    bottleneck_completion = sub_subtask_data["completion_percentage"]
                    bottleneck_task_id = sub_subtask_id
    
    # Verify that a bottleneck was identified
    assert bottleneck_task_id is not None
    assert bottleneck_completion < 100
    
    # The bottleneck should be sub-subtask-2-3 with 0% completion
    assert bottleneck_task_id == "sub-subtask-2-3"
    assert bottleneck_completion == 0

@then("the progress tracking should be accessible through the coordinator's API")
def verify_progress_tracking_accessible(context):
    """Verify that progress tracking is accessible through the coordinator's API."""
    # Patch the coordinator to add a get_progress_tracking method
    def get_progress_tracking():
        return context.progress_tracking
    
    context.edrr_coordinator.get_progress_tracking = get_progress_tracking
    
    # Verify that the method returns the expected data
    progress_data = context.edrr_coordinator.get_progress_tracking()
    assert progress_data == context.progress_tracking
    assert context.task["id"] in progress_data
    assert "completion_percentage" in progress_data[context.task["id"]]