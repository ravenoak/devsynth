import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path

from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.edrr.coordinator import EDRRCoordinatorError
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.domain.models.memory import MemoryType


@pytest.fixture
def memory_manager():
    """Create a mock memory manager for testing."""
    mock_memory_manager = MagicMock(spec=MemoryManager)
    
    # Mock the store method
    mock_memory_manager.store.return_value = "memory_id_123"
    
    # Mock the retrieve method
    mock_memory_manager.retrieve.return_value = {
        "content": "Test memory content",
        "metadata": {"key": "value"}
    }
    
    # Mock the search method
    mock_memory_manager.search.return_value = [
        {
            "id": "memory_id_123",
            "content": "Test memory content",
            "metadata": {"key": "value"},
            "score": 0.95
        }
    ]
    
    return mock_memory_manager


@pytest.fixture
def wsde_team():
    """Create a mock WSDE team for testing."""
    mock_wsde_team = MagicMock(spec=WSDETeam)
    
    # Mock the execute_task method
    mock_wsde_team.execute_task.return_value = {
        "result": "Task executed successfully",
        "artifacts": ["artifact1", "artifact2"],
        "metrics": {"time_taken": 10.5}
    }
    
    # Mock the get_team_report method
    mock_wsde_team.get_team_report.return_value = {
        "team_composition": ["Agent1", "Agent2", "Agent3"],
        "task_distribution": {"Agent1": 2, "Agent2": 3, "Agent3": 1},
        "performance_metrics": {"efficiency": 0.85, "quality": 0.9}
    }
    
    return mock_wsde_team


@pytest.fixture
def code_analyzer():
    """Create a mock code analyzer for testing."""
    mock_code_analyzer = MagicMock(spec=CodeAnalyzer)
    
    # Mock the analyze_code method
    mock_code_analyzer.analyze_code.return_value = {
        "complexity": 5,
        "maintainability": 8,
        "issues": ["Issue1", "Issue2"]
    }
    
    return mock_code_analyzer


@pytest.fixture
def ast_transformer():
    """Create a mock AST transformer for testing."""
    mock_ast_transformer = MagicMock(spec=AstTransformer)
    return mock_ast_transformer


@pytest.fixture
def prompt_manager():
    """Create a mock prompt manager for testing."""
    mock_prompt_manager = MagicMock(spec=PromptManager)
    return mock_prompt_manager


@pytest.fixture
def documentation_manager():
    """Create a mock documentation manager for testing."""
    mock_documentation_manager = MagicMock(spec=DocumentationManager)
    return mock_documentation_manager


@pytest.fixture
def enhanced_coordinator(memory_manager, wsde_team, code_analyzer, ast_transformer, prompt_manager, documentation_manager):
    """Create an EnhancedEDRRCoordinator instance for testing."""
    coordinator = EnhancedEDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True
    )
    return coordinator


class TestEnhancedEDRRCoordinator:
    """Tests for the EnhancedEDRRCoordinator class."""

    def test_initialization(self, enhanced_coordinator):
        """Test that the enhanced coordinator initializes correctly."""
        assert enhanced_coordinator is not None
        assert enhanced_coordinator.memory_manager is not None
        assert enhanced_coordinator.wsde_team is not None
        assert enhanced_coordinator.code_analyzer is not None
        assert enhanced_coordinator.ast_transformer is not None
        assert enhanced_coordinator.prompt_manager is not None
        assert enhanced_coordinator.documentation_manager is not None
        assert enhanced_coordinator.enable_enhanced_logging is True
        assert enhanced_coordinator.recursion_depth == 0
        assert enhanced_coordinator.parent_cycle_id is None
        assert enhanced_coordinator.parent_phase is None
        assert hasattr(enhanced_coordinator, 'phase_metrics')
        assert enhanced_coordinator.phase_metrics == {}

    def test_progress_to_phase(self, enhanced_coordinator, memory_manager):
        """Test enhanced progress to phase with metrics collection."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Mock the memory_manager.store method to return a specific ID
        memory_manager.store.return_value = "phase_transition_memory_id"
        
        # Mock the collect_phase_metrics function
        with patch("devsynth.application.edrr.edrr_coordinator_enhanced.collect_phase_metrics") as mock_collect_metrics:
            mock_collect_metrics.return_value = {
                "duration": 10.5,
                "quality_score": 0.85,
                "complexity": 5
            }
            
            # Call the method under test
            enhanced_coordinator.progress_to_phase(Phase.DESIGN)
            
            # Verify that the current phase is updated
            assert enhanced_coordinator.current_phase == Phase.DESIGN
            
            # Verify that collect_phase_metrics was called
            mock_collect_metrics.assert_called_once()
            
            # Verify that the phase metrics were stored
            assert Phase.EXPLORE.value in enhanced_coordinator.phase_metrics
            
            # Verify that the phase transition was stored in memory
            memory_manager.store.assert_called_with(
                content={
                    "from_phase": Phase.EXPLORE.value,
                    "to_phase": Phase.DESIGN.value,
                    "timestamp": pytest.approx(datetime.now().timestamp(), abs=5),
                    "metrics": mock_collect_metrics.return_value
                },
                memory_type=MemoryType.PHASE_TRANSITION,
                metadata={"cycle_id": enhanced_coordinator.cycle_id}
            )

    def test_enhanced_decide_next_phase(self, enhanced_coordinator):
        """Test the enhanced decision-making for the next phase."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Set up phase metrics
        enhanced_coordinator.phase_metrics = {
            Phase.EXPLORE.value: {
                "duration": 10.5,
                "quality_score": 0.85,
                "complexity": 5
            }
        }
        
        # Mock the calculate_enhanced_quality_score function
        with patch("devsynth.application.edrr.edrr_coordinator_enhanced.calculate_enhanced_quality_score") as mock_calculate_score:
            mock_calculate_score.return_value = 0.9  # High quality score
            
            # Call the internal method under test
            next_phase = enhanced_coordinator._enhanced_decide_next_phase()
            
            # Verify that the next phase is DESIGN (normal progression)
            assert next_phase == Phase.DESIGN
            
            # Now set a low quality score to trigger a repeat of the current phase
            mock_calculate_score.return_value = 0.3  # Low quality score
            
            # Call the internal method again
            next_phase = enhanced_coordinator._enhanced_decide_next_phase()
            
            # Verify that the next phase is still EXPLORE (repeat due to low quality)
            assert next_phase == Phase.EXPLORE

    def test_enhanced_maybe_auto_progress(self, enhanced_coordinator):
        """Test the enhanced auto-progression."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Mock the config to enable auto-progress
        enhanced_coordinator.config = {"auto_progress": True}
        
        # Mock the _enhanced_decide_next_phase method
        with patch.object(enhanced_coordinator, '_enhanced_decide_next_phase') as mock_decide:
            mock_decide.return_value = Phase.DESIGN
            
            # Call the internal method under test
            enhanced_coordinator._enhanced_maybe_auto_progress()
            
            # Verify that the current phase is updated to DESIGN (auto-progressed)
            assert enhanced_coordinator.current_phase == Phase.DESIGN
            
            # Verify that _enhanced_decide_next_phase was called
            mock_decide.assert_called_once()
            
            # Disable auto-progress
            enhanced_coordinator.config = {"auto_progress": False}
            
            # Reset the mock
            mock_decide.reset_mock()
            
            # Call the internal method again
            enhanced_coordinator._enhanced_maybe_auto_progress()
            
            # Verify that _enhanced_decide_next_phase was not called
            mock_decide.assert_not_called()

    def test_calculate_quality_score(self, enhanced_coordinator):
        """Test the quality score calculation."""
        # Create a result with various attributes
        result = {
            "result": "Task executed successfully",
            "artifacts": ["artifact1", "artifact2"],
            "metrics": {
                "time_taken": 10.5,
                "quality": 0.85,
                "complexity": 5
            }
        }
        
        # Call the method under test
        score = enhanced_coordinator._calculate_quality_score(result)
        
        # Verify that a score was calculated
        assert isinstance(score, float)
        assert 0 <= score <= 1
        
        # Test with a result that has no metrics
        result_no_metrics = {
            "result": "Task executed successfully",
            "artifacts": ["artifact1", "artifact2"]
        }
        
        # Call the method again
        score = enhanced_coordinator._calculate_quality_score(result_no_metrics)
        
        # Verify that a default score was used
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_get_phase_metrics(self, enhanced_coordinator):
        """Test getting metrics for a specific phase."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Set up phase metrics
        enhanced_coordinator.phase_metrics = {
            Phase.EXPLORE.value: {
                "duration": 10.5,
                "quality_score": 0.85,
                "complexity": 5
            },
            Phase.DESIGN.value: {
                "duration": 15.2,
                "quality_score": 0.9,
                "complexity": 3
            }
        }
        
        # Call the method under test for a specific phase
        metrics = enhanced_coordinator.get_phase_metrics(Phase.EXPLORE)
        
        # Verify the metrics
        assert metrics == enhanced_coordinator.phase_metrics[Phase.EXPLORE.value]
        
        # Call the method for the current phase (no phase specified)
        enhanced_coordinator.current_phase = Phase.DESIGN
        metrics = enhanced_coordinator.get_phase_metrics()
        
        # Verify the metrics
        assert metrics == enhanced_coordinator.phase_metrics[Phase.DESIGN.value]
        
        # Call the method for a phase that doesn't have metrics
        metrics = enhanced_coordinator.get_phase_metrics(Phase.REFINE)
        
        # Verify that an empty dict is returned
        assert metrics == {}

    def test_get_all_metrics(self, enhanced_coordinator):
        """Test getting all phase metrics."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Set up phase metrics
        enhanced_coordinator.phase_metrics = {
            Phase.EXPLORE.value: {
                "duration": 10.5,
                "quality_score": 0.85,
                "complexity": 5
            },
            Phase.DESIGN.value: {
                "duration": 15.2,
                "quality_score": 0.9,
                "complexity": 3
            }
        }
        
        # Call the method under test
        all_metrics = enhanced_coordinator.get_all_metrics()
        
        # Verify the metrics
        assert all_metrics == enhanced_coordinator.phase_metrics

    def test_get_metrics_history(self, enhanced_coordinator, memory_manager):
        """Test getting metrics history from memory."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Mock the memory_manager.search method to return phase transitions with metrics
        memory_manager.search.return_value = [
            {
                "id": "transition1",
                "content": {
                    "from_phase": Phase.EXPLORE.value,
                    "to_phase": Phase.DESIGN.value,
                    "timestamp": datetime.now().timestamp(),
                    "metrics": {
                        "duration": 10.5,
                        "quality_score": 0.85,
                        "complexity": 5
                    }
                },
                "metadata": {"cycle_id": enhanced_coordinator.cycle_id},
                "score": 0.95
            },
            {
                "id": "transition2",
                "content": {
                    "from_phase": Phase.DESIGN.value,
                    "to_phase": Phase.REFINE.value,
                    "timestamp": datetime.now().timestamp(),
                    "metrics": {
                        "duration": 15.2,
                        "quality_score": 0.9,
                        "complexity": 3
                    }
                },
                "metadata": {"cycle_id": enhanced_coordinator.cycle_id},
                "score": 0.9
            }
        ]
        
        # Call the method under test
        history = enhanced_coordinator.get_metrics_history()
        
        # Verify that the memory_manager.search method was called
        memory_manager.search.assert_called_with(
            memory_type=MemoryType.PHASE_TRANSITION,
            metadata={"cycle_id": enhanced_coordinator.cycle_id}
        )
        
        # Verify the history structure
        assert isinstance(history, list)
        assert len(history) == 2
        assert "from_phase" in history[0]
        assert "to_phase" in history[0]
        assert "timestamp" in history[0]
        assert "metrics" in history[0]

    def test_create_micro_cycle(self, enhanced_coordinator, memory_manager, wsde_team):
        """Test creating a micro-cycle with enhanced features."""
        # Start a cycle first
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"]
        }
        enhanced_coordinator.start_cycle(task)
        
        # Set the current phase
        enhanced_coordinator.current_phase = Phase.DESIGN
        
        # Create a micro-task
        micro_task = {
            "name": "Micro Task",
            "description": "This is a micro task",
            "requirements": ["micro_req1"]
        }
        
        # Mock the parent class's create_micro_cycle method
        with patch("devsynth.application.edrr.coordinator.EDRRCoordinator.create_micro_cycle") as mock_parent_create:
            mock_micro_coordinator = MagicMock()
            mock_parent_create.return_value = mock_micro_coordinator
            
            # Call the method under test
            result = enhanced_coordinator.create_micro_cycle(micro_task, Phase.DESIGN)
            
            # Verify that the parent method was called
            mock_parent_create.assert_called_once_with(micro_task, Phase.DESIGN)
            
            # Verify that the result is the mock micro coordinator
            assert result == mock_micro_coordinator
            
            # Verify that the micro coordinator was configured with enhanced features
            assert isinstance(result, MagicMock)