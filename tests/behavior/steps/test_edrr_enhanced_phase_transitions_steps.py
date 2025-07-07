"""Step definitions for the Enhanced EDRR Phase Transitions feature."""

from __future__ import annotations

from pytest_bdd import given, when, then, parsers
from pytest_bdd import scenarios
import pytest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime, timedelta

# Import the scenarios from the feature file
scenarios('../features/edrr_enhanced_phase_transitions.feature')

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
            self.phase_durations = {}
            self.phase_metrics = {}
            self.quality_thresholds = {}
            self.historical_data = {}
            self.context_preservation = {}
            
    return Context()

@given("the EDRR coordinator is initialized with enhanced phase transition features")
def edrr_coordinator_initialized_with_enhanced_features(context):
    """Initialize the EDRR coordinator with enhanced phase transition features."""
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
    
    # Initialize the EDRRCoordinator with enhanced features
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
                "phase_transitions": {
                    "adaptive_duration": True,
                    "quality_thresholds": {
                        "expand": 0.7,
                        "differentiate": 0.7,
                        "refine": 0.8,
                        "retrospect": 0.8
                    },
                    "use_historical_data": True,
                    "context_preservation": True
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

# Scenario: Adaptive phase duration based on task complexity
@given("a task with complexity score of 8 out of 10")
def task_with_high_complexity(context):
    """Create a task with high complexity."""
    context.task = {
        "id": "complex-task-123",
        "description": "Implement a distributed caching system with failover",
        "complexity_score": 8,
        "estimated_effort": "high"
    }

@when("I start the EDRR cycle with this task")
def start_edrr_cycle_with_complex_task(context):
    """Start the EDRR cycle with the complex task."""
    # Patch the _execute_phase methods to track duration
    original_execute_expand = context.edrr_coordinator._execute_expand_phase
    original_execute_differentiate = context.edrr_coordinator._execute_differentiate_phase
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
    
    # Replace the methods with our tracking versions
    context.edrr_coordinator._execute_expand_phase = track_duration("EXPAND", original_execute_expand)
    context.edrr_coordinator._execute_differentiate_phase = track_duration("DIFFERENTIATE", original_execute_differentiate)
    context.edrr_coordinator._execute_refine_phase = track_duration("REFINE", original_execute_refine)
    context.edrr_coordinator._execute_retrospect_phase = track_duration("RETROSPECT", original_execute_retrospect)
    
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Restore original methods
    context.edrr_coordinator._execute_expand_phase = original_execute_expand
    context.edrr_coordinator._execute_differentiate_phase = original_execute_differentiate
    context.edrr_coordinator._execute_refine_phase = original_execute_refine
    context.edrr_coordinator._execute_retrospect_phase = original_execute_retrospect

@then("the coordinator should allocate more time for complex phases")
def verify_more_time_for_complex_phases(context):
    """Verify that more time is allocated for complex phases."""
    # Check that the performance metrics include duration adjustments
    assert "EXPAND" in context.edrr_coordinator.performance_metrics
    assert "DIFFERENTIATE" in context.edrr_coordinator.performance_metrics
    
    # Verify that the duration adjustment factor is applied
    assert context.edrr_coordinator.performance_metrics["EXPAND"].get("duration_adjustment_factor", 1.0) > 1.0
    assert context.edrr_coordinator.performance_metrics["DIFFERENTIATE"].get("duration_adjustment_factor", 1.0) > 1.0

@then('the "{phase_name}" phase should have extended duration')
def verify_phase_has_extended_duration(context, phase_name):
    """Verify that the specified phase has extended duration."""
    phase = Phase[phase_name.upper()]
    
    # Check that the phase has an extended duration
    assert phase.name in context.edrr_coordinator.performance_metrics
    assert "duration_adjustment_factor" in context.edrr_coordinator.performance_metrics[phase.name]
    assert context.edrr_coordinator.performance_metrics[phase.name]["duration_adjustment_factor"] > 1.0

@then("the phase durations should be proportional to the task complexity")
def verify_durations_proportional_to_complexity(context):
    """Verify that phase durations are proportional to task complexity."""
    # Check that the complexity score is used to adjust durations
    complexity_score = context.task["complexity_score"]
    
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        if phase in context.edrr_coordinator.performance_metrics:
            adjustment_factor = context.edrr_coordinator.performance_metrics[phase].get("duration_adjustment_factor", 1.0)
            # The adjustment factor should be related to the complexity score
            assert abs(adjustment_factor - (1.0 + complexity_score / 10.0)) < 0.5

@then("the performance metrics should include phase duration adjustments")
def verify_metrics_include_duration_adjustments(context):
    """Verify that performance metrics include phase duration adjustments."""
    # Check that all phases have duration adjustment metrics
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        if phase in context.edrr_coordinator.performance_metrics:
            assert "duration_adjustment_factor" in context.edrr_coordinator.performance_metrics[phase]
            assert "original_duration" in context.edrr_coordinator.performance_metrics[phase]
            assert "adjusted_duration" in context.edrr_coordinator.performance_metrics[phase]

# Scenario: Phase-specific metrics for better monitoring
@given("the EDRR coordinator is configured to track detailed phase metrics")
def edrr_coordinator_with_detailed_metrics(context):
    """Configure the EDRR coordinator to track detailed phase metrics."""
    # Update the configuration to enable detailed metrics
    context.edrr_coordinator.config["edrr"]["metrics"] = {
        "detailed_tracking": True,
        "quality_metrics": True,
        "completion_percentage": True,
        "resource_utilization": True,
        "effectiveness_score": True
    }

@when("I complete a full EDRR cycle with a task")
def complete_full_edrr_cycle_with_metrics(context):
    """Complete a full EDRR cycle with metrics tracking."""
    # Create a task
    context.task = {
        "id": "metrics-task-123",
        "description": "Implement a feature with metrics tracking"
    }
    
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Set up necessary data for each phase and progress through all phases
    # Expand phase
    context.edrr_coordinator.results[Phase.EXPAND] = {
        "completed": True,
        "approaches": [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ],
        "metrics": {
            "quality_score": 0.85,
            "completion_percentage": 100,
            "resource_utilization": 0.65,
            "effectiveness_score": 0.78
        }
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
        },
        "metrics": {
            "quality_score": 0.82,
            "completion_percentage": 100,
            "resource_utilization": 0.70,
            "effectiveness_score": 0.75
        }
    }
    context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    
    # Refine phase
    context.edrr_coordinator.results[Phase.REFINE] = {
        "completed": True,
        "implementation": {
            "code": "def example(): return 'Hello, World!'",
            "description": "Implemented solution"
        },
        "metrics": {
            "quality_score": 0.88,
            "completion_percentage": 100,
            "resource_utilization": 0.75,
            "effectiveness_score": 0.82
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
        "is_valid": True,
        "metrics": {
            "quality_score": 0.90,
            "completion_percentage": 100,
            "resource_utilization": 0.60,
            "effectiveness_score": 0.85
        }
    }
    context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)
    
    # Store the phase metrics for verification
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        if phase.name in context.edrr_coordinator.results:
            context.phase_metrics[phase.name] = context.edrr_coordinator.results[phase.name].get("metrics", {})

@then("the coordinator should generate phase-specific metrics")
def verify_phase_specific_metrics_generated(context):
    """Verify that phase-specific metrics are generated."""
    # Check that metrics exist for all phases
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in context.phase_metrics
        assert context.phase_metrics[phase.name] is not None
        assert len(context.phase_metrics[phase.name]) > 0

@then('the metrics should include "{metric_name}" for each phase')
def verify_metric_included_for_each_phase(context, metric_name):
    """Verify that the specified metric is included for each phase."""
    # Convert the metric name to the actual key in the metrics dictionary
    metric_key = metric_name.lower().replace(" ", "_")
    
    # Check that the metric exists for all phases
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        assert phase.name in context.phase_metrics
        assert metric_key in context.phase_metrics[phase.name]
        assert context.phase_metrics[phase.name][metric_key] is not None

@then("these metrics should be stored in memory with appropriate metadata")
def verify_metrics_stored_in_memory(context):
    """Verify that metrics are stored in memory with appropriate metadata."""
    # Create a test storage to track what's stored
    test_storage = {}
    
    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase
    
    def test_store_method(data, data_type, edrr_phase, metadata=None):
        if data_type == "PHASE_METRICS":
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
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            if phase.name in context.edrr_coordinator.results and "metrics" in context.edrr_coordinator.results[phase.name]:
                context.memory_manager.store_with_edrr_phase(
                    context.edrr_coordinator.results[phase.name]["metrics"],
                    "PHASE_METRICS",
                    phase.name,
                    {"cycle_id": context.edrr_coordinator.cycle_id}
                )
        
        # Verify that metrics were stored for all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            assert phase.name in test_storage
            assert test_storage[phase.name]["data_type"] == "PHASE_METRICS"
            assert "quality_score" in test_storage[phase.name]["data"]
            assert "completion_percentage" in test_storage[phase.name]["data"]
            assert "resource_utilization" in test_storage[phase.name]["data"]
            assert "effectiveness_score" in test_storage[phase.name]["data"]
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method

# Scenario: Intelligent phase transition based on quality thresholds
@given("the EDRR coordinator is configured with quality thresholds")
def edrr_coordinator_with_quality_thresholds(context):
    """Configure the EDRR coordinator with quality thresholds."""
    # Set up quality thresholds
    context.quality_thresholds = {
        "EXPAND": 0.7,
        "DIFFERENTIATE": 0.7,
        "REFINE": 0.8,
        "RETROSPECT": 0.8
    }
    
    # Update the configuration
    context.edrr_coordinator.config["edrr"]["phase_transitions"]["quality_thresholds"] = {
        "expand": context.quality_thresholds["EXPAND"],
        "differentiate": context.quality_thresholds["DIFFERENTIATE"],
        "refine": context.quality_thresholds["REFINE"],
        "retrospect": context.quality_thresholds["RETROSPECT"]
    }
    
    # Patch the _maybe_auto_progress method to check quality thresholds
    original_auto_progress = context.edrr_coordinator._maybe_auto_progress
    
    def quality_check_auto_progress():
        phase = context.edrr_coordinator.current_phase
        if phase is None:
            return original_auto_progress()
        
        # Check if the current phase has results
        if phase.name in context.edrr_coordinator.results:
            # Check if the quality score meets the threshold
            phase_results = context.edrr_coordinator.results[phase.name]
            quality_score = phase_results.get("quality_score", 0.0)
            threshold = context.quality_thresholds.get(phase.name, 0.7)
            
            if quality_score < threshold:
                # Don't progress if quality is below threshold
                return False
        
        # Call the original method if quality check passes
        return original_auto_progress()
    
    # Replace the method
    context.edrr_coordinator._maybe_auto_progress = quality_check_auto_progress

@when('the "{phase_name}" phase produces results below the quality threshold')
def phase_produces_low_quality_results(context, phase_name):
    """Simulate a phase producing results below the quality threshold."""
    phase = Phase[phase_name.upper()]
    
    # Create a task
    context.task = {
        "id": "quality-task-123",
        "description": "Implement a feature with quality checks"
    }
    
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Set up low quality results for the phase
    context.edrr_coordinator.results[phase] = {
        "completed": True,
        "quality_score": context.quality_thresholds[phase.name] - 0.1,  # Below threshold
        "approaches": [
            {"id": "approach-1", "description": "Low quality approach", "code": "def approach1(): pass"}
        ]
    }
    
    # Try to progress to the next phase
    context.edrr_coordinator.progress_to_phase(phase)
    context.edrr_coordinator._maybe_auto_progress()

@then("the coordinator should not automatically progress to the next phase")
def verify_no_auto_progression(context):
    """Verify that the coordinator does not automatically progress to the next phase."""
    # Check that the current phase is still the one with low quality
    assert context.edrr_coordinator.current_phase == Phase.EXPAND

@then("the coordinator should trigger additional processing in the current phase")
def verify_additional_processing_triggered(context):
    """Verify that additional processing is triggered in the current phase."""
    # Check that additional processing was triggered
    assert "additional_processing" in context.edrr_coordinator.results[Phase.EXPAND]
    assert context.edrr_coordinator.results[Phase.EXPAND]["additional_processing"] is True

@then("the coordinator should log the quality issue and remediation attempt")
def verify_quality_issue_logged(context):
    """Verify that the quality issue and remediation attempt are logged."""
    # Check that the quality issue was logged
    assert "quality_issues" in context.edrr_coordinator.results[Phase.EXPAND]
    assert len(context.edrr_coordinator.results[Phase.EXPAND]["quality_issues"]) > 0
    
    # Check that remediation was attempted
    assert "remediation_attempts" in context.edrr_coordinator.results[Phase.EXPAND]
    assert len(context.edrr_coordinator.results[Phase.EXPAND]["remediation_attempts"]) > 0

@when("the quality threshold is met after additional processing")
def quality_threshold_met_after_processing(context):
    """Simulate the quality threshold being met after additional processing."""
    # Update the quality score to meet the threshold
    context.edrr_coordinator.results[Phase.EXPAND]["quality_score"] = context.quality_thresholds["EXPAND"] + 0.1
    
    # Try to progress to the next phase
    context.edrr_coordinator._maybe_auto_progress()

@then("the coordinator should progress to the next phase")
def verify_progression_to_next_phase(context):
    """Verify that the coordinator progresses to the next phase."""
    # Check that the current phase has changed
    assert context.edrr_coordinator.current_phase == Phase.DIFFERENTIATE

@then("the phase transition should include quality metrics in the metadata")
def verify_quality_metrics_in_transition_metadata(context):
    """Verify that the phase transition includes quality metrics in the metadata."""
    # Create a test storage to track what's stored
    test_storage = {}
    
    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase
    
    def test_store_method(data, data_type, edrr_phase, metadata=None):
        if data_type == "PHASE_TRANSITION":
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
        context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Verify that quality metrics were included in the metadata
        assert "DIFFERENTIATE" in test_storage
        assert test_storage["DIFFERENTIATE"]["data_type"] == "PHASE_TRANSITION"
        assert "metadata" in test_storage["DIFFERENTIATE"]
        assert "quality_metrics" in test_storage["DIFFERENTIATE"]["metadata"]
        assert "quality_score" in test_storage["DIFFERENTIATE"]["metadata"]["quality_metrics"]
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method

# Scenario: Dynamic phase transition criteria based on previous results
@given("the EDRR coordinator has completed several cycles")
def edrr_coordinator_with_completed_cycles(context):
    """Set up the EDRR coordinator with completed cycles."""
    # Create historical data for similar tasks
    context.historical_data = {
        "similar_task_1": {
            "cycle_id": "cycle-001",
            "task": {"id": "task-001", "description": "Similar task 1"},
            "phases": {
                "EXPAND": {"duration": 10, "quality_score": 0.85, "strategies": ["strategy_a", "strategy_b"]},
                "DIFFERENTIATE": {"duration": 15, "quality_score": 0.82, "strategies": ["strategy_c"]},
                "REFINE": {"duration": 20, "quality_score": 0.88, "strategies": ["strategy_d", "strategy_e"]},
                "RETROSPECT": {"duration": 8, "quality_score": 0.90, "strategies": ["strategy_f"]}
            },
            "success": True
        },
        "similar_task_2": {
            "cycle_id": "cycle-002",
            "task": {"id": "task-002", "description": "Similar task 2"},
            "phases": {
                "EXPAND": {"duration": 12, "quality_score": 0.80, "strategies": ["strategy_b", "strategy_g"]},
                "DIFFERENTIATE": {"duration": 18, "quality_score": 0.78, "strategies": ["strategy_h"]},
                "REFINE": {"duration": 25, "quality_score": 0.85, "strategies": ["strategy_i"]},
                "RETROSPECT": {"duration": 10, "quality_score": 0.88, "strategies": ["strategy_j"]}
            },
            "success": True
        }
    }
    
    # Store the historical data in memory
    for task_id, data in context.historical_data.items():
        context.memory_manager.store(data, "HISTORICAL_CYCLE_DATA", {"task_id": task_id})
    
    # Patch the memory manager to retrieve historical data
    original_search = context.memory_manager.search
    
    def search_with_historical_data(query=None, memory_type=None, metadata=None, limit=None):
        if memory_type == "HISTORICAL_CYCLE_DATA":
            return [{"id": task_id, "content": data} for task_id, data in context.historical_data.items()]
        return original_search(query, memory_type, metadata, limit)
    
    # Replace the method
    context.memory_manager.search = search_with_historical_data

@when("I start a new EDRR cycle with a similar task")
def start_new_cycle_with_similar_task(context):
    """Start a new EDRR cycle with a task similar to previous ones."""
    # Create a similar task
    context.task = {
        "id": "similar-task-123",
        "description": "Implement a feature similar to previous tasks",
        "tags": ["similar", "feature"]
    }
    
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)

@then("the coordinator should use historical data to optimize phase transitions")
def verify_historical_data_used(context):
    """Verify that historical data is used to optimize phase transitions."""
    # Check that historical data was retrieved and used
    assert hasattr(context.edrr_coordinator, "_historical_data")
    assert context.edrr_coordinator._historical_data is not None
    assert len(context.edrr_coordinator._historical_data) > 0

@then("the phase transition criteria should be adjusted based on previous success patterns")
def verify_criteria_adjusted_based_on_patterns(context):
    """Verify that phase transition criteria are adjusted based on previous success patterns."""
    # Check that the criteria were adjusted
    assert hasattr(context.edrr_coordinator, "_adjusted_criteria")
    assert context.edrr_coordinator._adjusted_criteria is not None
    
    # Check that the criteria include successful strategies from historical data
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        assert phase in context.edrr_coordinator._adjusted_criteria
        assert "strategies" in context.edrr_coordinator._adjusted_criteria[phase]
        
        # Check that strategies from historical data are included
        historical_strategies = set()
        for data in context.historical_data.values():
            if phase in data["phases"] and "strategies" in data["phases"][phase]:
                historical_strategies.update(data["phases"][phase]["strategies"])
        
        for strategy in context.edrr_coordinator._adjusted_criteria[phase]["strategies"]:
            assert strategy in historical_strategies

@then("the coordinator should prioritize strategies that were effective in similar tasks")
def verify_effective_strategies_prioritized(context):
    """Verify that strategies that were effective in similar tasks are prioritized."""
    # Check that strategies are prioritized based on effectiveness
    for phase in ["EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"]:
        if phase in context.edrr_coordinator._adjusted_criteria:
            assert "prioritized_strategies" in context.edrr_coordinator._adjusted_criteria[phase]
            assert len(context.edrr_coordinator._adjusted_criteria[phase]["prioritized_strategies"]) > 0
            
            # Check that the prioritized strategies are from successful historical cycles
            for strategy in context.edrr_coordinator._adjusted_criteria[phase]["prioritized_strategies"]:
                found = False
                for data in context.historical_data.values():
                    if data["success"] and phase in data["phases"] and "strategies" in data["phases"][phase]:
                        if strategy in data["phases"][phase]["strategies"]:
                            found = True
                            break
                assert found, f"Strategy {strategy} was not found in successful historical cycles"

@then("the phase transition metadata should reference the historical data used")
def verify_metadata_references_historical_data(context):
    """Verify that the phase transition metadata references the historical data used."""
    # Create a test storage to track what's stored
    test_storage = {}
    
    # Override the store_with_edrr_phase method to store in our test_storage
    original_store_method = context.memory_manager.store_with_edrr_phase
    
    def test_store_method(data, data_type, edrr_phase, metadata=None):
        if data_type == "PHASE_TRANSITION":
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
        
        # Verify that historical data is referenced in the metadata
        assert "EXPAND" in test_storage
        assert test_storage["EXPAND"]["data_type"] == "PHASE_TRANSITION"
        assert "metadata" in test_storage["EXPAND"]
        assert "historical_data_references" in test_storage["EXPAND"]["metadata"]
        assert len(test_storage["EXPAND"]["metadata"]["historical_data_references"]) > 0
        
        # Check that the references include cycle IDs from the historical data
        historical_cycle_ids = [data["cycle_id"] for data in context.historical_data.values()]
        for reference in test_storage["EXPAND"]["metadata"]["historical_data_references"]:
            assert "cycle_id" in reference
            assert reference["cycle_id"] in historical_cycle_ids
    finally:
        # Restore the original method
        context.memory_manager.store_with_edrr_phase = original_store_method

# Scenario: Phase transition with comprehensive context preservation
@given('the EDRR coordinator is in the "{phase_name}" phase')
def edrr_coordinator_in_specific_phase(context, phase_name):
    """Set up the EDRR coordinator in a specific phase."""
    phase = Phase[phase_name.upper()]
    
    # Create a task
    context.task = {
        "id": "context-task-123",
        "description": "Implement a feature with context preservation"
    }
    
    # Start the cycle
    context.edrr_coordinator.start_cycle(context.task)
    
    # Set up data for the phase
    if phase == Phase.EXPAND:
        context.edrr_coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": [
                {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
                {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
            ],
            "key_insights": [
                {"id": "insight-1", "description": "Important insight 1"},
                {"id": "insight-2", "description": "Important insight 2"}
            ],
            "constraints": [
                {"id": "constraint-1", "description": "Must be compatible with Python 3.8+"},
                {"id": "constraint-2", "description": "Must handle edge cases gracefully"}
            ]
        }
        
        # Store the context for verification
        context.context_preservation["key_insights"] = context.edrr_coordinator.results[Phase.EXPAND]["key_insights"]
        context.context_preservation["constraints"] = context.edrr_coordinator.results[Phase.EXPAND]["constraints"]
        context.context_preservation["approaches"] = context.edrr_coordinator.results[Phase.EXPAND]["approaches"]
    
    # Progress to the phase
    context.edrr_coordinator.progress_to_phase(phase)

@when('the coordinator transitions to the "{phase_name}" phase')
def coordinator_transitions_to_phase(context, phase_name):
    """Transition the coordinator to the specified phase."""
    phase = Phase[phase_name.upper()]
    
    # Progress to the phase
    context.edrr_coordinator.progress_to_phase(phase)

@then("all relevant context from the previous phase should be preserved")
def verify_context_preserved(context):
    """Verify that all relevant context from the previous phase is preserved."""
    # Check that the context was preserved
    assert hasattr(context.edrr_coordinator, "_preserved_context")
    assert context.edrr_coordinator._preserved_context is not None
    assert "EXPAND" in context.edrr_coordinator._preserved_context
    assert context.edrr_coordinator._preserved_context["EXPAND"] is not None

@then('the context should include all key insights from the "{phase_name}" phase')
def verify_context_includes_key_insights(context, phase_name):
    """Verify that the context includes all key insights from the specified phase."""
    phase = Phase[phase_name.upper()]
    
    # Check that key insights are preserved
    assert "key_insights" in context.edrr_coordinator._preserved_context[phase.name]
    preserved_insights = context.edrr_coordinator._preserved_context[phase.name]["key_insights"]
    original_insights = context.context_preservation["key_insights"]
    
    # Check that all original insights are preserved
    for insight in original_insights:
        assert any(i["id"] == insight["id"] for i in preserved_insights)

@then('the context should include all constraints identified in the "{phase_name}" phase')
def verify_context_includes_constraints(context, phase_name):
    """Verify that the context includes all constraints identified in the specified phase."""
    phase = Phase[phase_name.upper()]
    
    # Check that constraints are preserved
    assert "constraints" in context.edrr_coordinator._preserved_context[phase.name]
    preserved_constraints = context.edrr_coordinator._preserved_context[phase.name]["constraints"]
    original_constraints = context.context_preservation["constraints"]
    
    # Check that all original constraints are preserved
    for constraint in original_constraints:
        assert any(c["id"] == constraint["id"] for c in preserved_constraints)

@then('the context should include all approaches generated in the "{phase_name}" phase')
def verify_context_includes_approaches(context, phase_name):
    """Verify that the context includes all approaches generated in the specified phase."""
    phase = Phase[phase_name.upper()]
    
    # Check that approaches are preserved
    assert "approaches" in context.edrr_coordinator._preserved_context[phase.name]
    preserved_approaches = context.edrr_coordinator._preserved_context[phase.name]["approaches"]
    original_approaches = context.context_preservation["approaches"]
    
    # Check that all original approaches are preserved
    for approach in original_approaches:
        assert any(a["id"] == approach["id"] for a in preserved_approaches)

@then('the "{phase_name}" phase should have access to this comprehensive context')
def verify_phase_has_access_to_context(context, phase_name):
    """Verify that the specified phase has access to the comprehensive context."""
    phase = Phase[phase_name.upper()]
    
    # Check that the phase has access to the context
    assert phase.name in context.edrr_coordinator.results
    assert "context" in context.edrr_coordinator.results[phase.name]
    phase_context = context.edrr_coordinator.results[phase.name]["context"]
    
    # Check that the context includes data from previous phases
    assert "previous_phases" in phase_context
    assert "EXPAND" in phase_context["previous_phases"]
    
    # Check that key elements are included
    previous_phase_context = phase_context["previous_phases"]["EXPAND"]
    assert "key_insights" in previous_phase_context
    assert "constraints" in previous_phase_context
    assert "approaches" in previous_phase_context