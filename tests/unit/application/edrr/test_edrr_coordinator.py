"""
Unit tests for the EDRR Coordinator.
"""
import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from devsynth.methodology.base import Phase
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.edrr.manifest_parser import ManifestParser
from devsynth.exceptions import EDRRCoordinatorError


class TestEDRRCoordinator:
    """Tests for the EDRRCoordinator class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for the EDRRCoordinator."""
        memory_manager = MagicMock()
        wsde_team = MagicMock()
        code_analyzer = MagicMock()
        ast_transformer = MagicMock()
        prompt_manager = MagicMock()
        documentation_manager = MagicMock()

        return {
            "memory_manager": memory_manager,
            "wsde_team": wsde_team,
            "code_analyzer": code_analyzer,
            "ast_transformer": ast_transformer,
            "prompt_manager": prompt_manager,
            "documentation_manager": documentation_manager
        }

    @pytest.fixture
    def coordinator(self, mock_dependencies):
        """Create an EDRRCoordinator instance for testing."""
        return EDRRCoordinator(
            memory_manager=mock_dependencies["memory_manager"],
            wsde_team=mock_dependencies["wsde_team"],
            code_analyzer=mock_dependencies["code_analyzer"],
            ast_transformer=mock_dependencies["ast_transformer"],
            prompt_manager=mock_dependencies["prompt_manager"],
            documentation_manager=mock_dependencies["documentation_manager"]
        )

    @pytest.fixture
    def enhanced_coordinator(self, mock_dependencies):
        """Create an EDRRCoordinator instance with enhanced logging for testing."""
        return EDRRCoordinator(
            memory_manager=mock_dependencies["memory_manager"],
            wsde_team=mock_dependencies["wsde_team"],
            code_analyzer=mock_dependencies["code_analyzer"],
            ast_transformer=mock_dependencies["ast_transformer"],
            prompt_manager=mock_dependencies["prompt_manager"],
            documentation_manager=mock_dependencies["documentation_manager"],
            enable_enhanced_logging=True
        )

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return {
            "id": "task-123",
            "description": "Implement a feature",
            "code": "def example(): pass"
        }

    @pytest.fixture
    def sample_manifest(self):
        """Create a sample manifest for testing."""
        return {
            "id": "manifest-123",
            "description": "Test manifest",
            "metadata": {
                "version": "1.0",
                "author": "Test Author"
            },
            "phases": {
                "expand": {
                    "instructions": "Brainstorm approaches",
                    "templates": ["expand_template"],
                    "resources": ["resource1"],
                    "dependencies": []
                },
                "differentiate": {
                    "instructions": "Evaluate approaches",
                    "templates": ["differentiate_template"],
                    "resources": ["resource2"],
                    "dependencies": ["expand"]
                },
                "refine": {
                    "instructions": "Implement solution",
                    "templates": ["refine_template"],
                    "resources": ["resource3"],
                    "dependencies": ["differentiate"]
                },
                "retrospect": {
                    "instructions": "Evaluate implementation",
                    "templates": ["retrospect_template"],
                    "resources": ["resource4"],
                    "dependencies": ["refine"]
                }
            }
        }

    def test_initialization(self, coordinator, mock_dependencies):
        """Test initialization of the EDRRCoordinator."""
        assert coordinator.memory_manager == mock_dependencies["memory_manager"]
        assert coordinator.wsde_team == mock_dependencies["wsde_team"]
        assert coordinator.code_analyzer == mock_dependencies["code_analyzer"]
        assert coordinator.ast_transformer == mock_dependencies["ast_transformer"]
        assert coordinator.prompt_manager == mock_dependencies["prompt_manager"]
        assert coordinator.documentation_manager == mock_dependencies["documentation_manager"]
        assert coordinator.current_phase is None
        assert coordinator.task is None
        assert coordinator.cycle_id is None
        assert coordinator.results == {}
        assert coordinator.manifest_parser is not None
        assert coordinator._enable_enhanced_logging is False

    def test_initialization_with_enhanced_logging(self, enhanced_coordinator):
        """Test initialization of the EDRRCoordinator with enhanced logging."""
        assert enhanced_coordinator._enable_enhanced_logging is True
        assert hasattr(enhanced_coordinator, "_execution_traces")
        assert enhanced_coordinator._execution_traces is not None

    def test_start_cycle(self, coordinator, sample_task, mock_dependencies):
        """Test starting an EDRR cycle."""
        # Patch the progress_to_phase method to prevent it from being called
        with patch.object(coordinator, 'progress_to_phase') as mock_progress:
            coordinator.start_cycle(sample_task)

            assert coordinator.task == sample_task
            assert coordinator.cycle_id is not None
            # Don't check current_phase as it's set by progress_to_phase
            # Don't check results as it's populated by progress_to_phase

            # Check that the task was stored in memory
            mock_dependencies["memory_manager"].store_with_edrr_phase.assert_called_with(
                sample_task, "TASK", "EXPAND", {"cycle_id": coordinator.cycle_id}
            )

            # Check that progress_to_phase was called with EXPAND
            mock_progress.assert_called_once_with(Phase.EXPAND)

    def test_progress_to_phase(self, coordinator, sample_task, mock_dependencies):
        """Test progressing to a phase."""
        coordinator.start_cycle(sample_task)

        # Reset the mock to clear the call history
        mock_dependencies["memory_manager"].reset_mock()

        # Progress to DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)

        assert coordinator.current_phase == Phase.DIFFERENTIATE

        # Check that the phase transition was stored in memory
        mock_dependencies["memory_manager"].store_with_edrr_phase.assert_any_call(
            {"from": "EXPAND", "to": "DIFFERENTIATE"}, 
            "PHASE_TRANSITION", 
            "DIFFERENTIATE", 
            {"cycle_id": coordinator.cycle_id}
        )

    def test_execute_expand_phase(self, coordinator, sample_task, mock_dependencies):
        """Test executing the EXPAND phase."""
        coordinator.start_cycle(sample_task)

        # Mock the WSDE team to return some approaches
        approaches = [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ]
        mock_dependencies["wsde_team"].brainstorm_approaches.return_value = approaches

        # Execute the EXPAND phase
        coordinator._execute_expand_phase()

        # Check that the WSDE team was called
        mock_dependencies["wsde_team"].brainstorm_approaches.assert_called_with(sample_task)

        # Check that the results were stored
        assert Phase.EXPAND in coordinator.results
        assert "wsde_brainstorm" in coordinator.results[Phase.EXPAND]
        assert coordinator.results[Phase.EXPAND]["wsde_brainstorm"] == approaches

    def test_execute_differentiate_phase(self, coordinator, sample_task, mock_dependencies):
        """Test executing the DIFFERENTIATE phase."""
        coordinator.start_cycle(sample_task)

        # Set up EXPAND phase results
        approaches = [
            {"id": "approach-1", "description": "First approach", "code": "def approach1(): pass"},
            {"id": "approach-2", "description": "Second approach", "code": "def approach2(): pass"}
        ]
        coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": approaches
        }

        # Mock the WSDE team to return an evaluation
        evaluation = {
            "selected_approach": approaches[0],
            "rationale": "This approach is better"
        }
        mock_dependencies["wsde_team"].evaluate_approaches.return_value = evaluation

        # Progress to DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)

        # Execute the DIFFERENTIATE phase
        coordinator._execute_differentiate_phase()

        # Check that the WSDE team was called
        mock_dependencies["wsde_team"].evaluate_approaches.assert_called_with(approaches)

        # Check that the results were stored
        assert Phase.DIFFERENTIATE in coordinator.results
        assert "evaluation" in coordinator.results[Phase.DIFFERENTIATE]
        assert coordinator.results[Phase.DIFFERENTIATE]["evaluation"] == evaluation

    def test_execute_refine_phase(self, coordinator, sample_task, mock_dependencies):
        """Test executing the REFINE phase."""
        coordinator.start_cycle(sample_task)

        # Set up DIFFERENTIATE phase results
        selected_approach = {
            "id": "approach-1",
            "description": "First approach",
            "code": "def approach1(): pass"
        }
        coordinator.results[Phase.DIFFERENTIATE] = {
            "completed": True,
            "evaluation": {
                "selected_approach": selected_approach,
                "rationale": "This approach is better"
            }
        }

        # Mock the WSDE team to return an implementation
        implementation = {
            "code": "def approach1_improved(): return 'Hello, World!'",
            "description": "Improved implementation"
        }
        mock_dependencies["wsde_team"].implement_approach.return_value = implementation

        # Progress to REFINE phase
        coordinator.progress_to_phase(Phase.REFINE)

        # Execute the REFINE phase
        coordinator._execute_refine_phase()

        # Check that the WSDE team was called
        mock_dependencies["wsde_team"].implement_approach.assert_called_with(selected_approach)

        # Check that the results were stored
        assert Phase.REFINE in coordinator.results
        assert "implementation" in coordinator.results[Phase.REFINE]
        assert coordinator.results[Phase.REFINE]["implementation"] == implementation

    def test_execute_retrospect_phase(self, coordinator, sample_task, mock_dependencies):
        """Test executing the RETROSPECT phase."""
        coordinator.start_cycle(sample_task)

        # Set up REFINE phase results
        implementation = {
            "code": "def approach1_improved(): return 'Hello, World!'",
            "description": "Improved implementation"
        }
        coordinator.results[Phase.REFINE] = {
            "completed": True,
            "implementation": implementation
        }

        # Mock the WSDE team to return an evaluation
        evaluation = {
            "quality": "good",
            "issues": [],
            "suggestions": []
        }
        mock_dependencies["wsde_team"].evaluate_implementation.return_value = evaluation

        # Progress to RETROSPECT phase
        coordinator.progress_to_phase(Phase.RETROSPECT)

        # Execute the RETROSPECT phase
        coordinator._execute_retrospect_phase()

        # Check that the WSDE team was called
        mock_dependencies["wsde_team"].evaluate_implementation.assert_called_with(implementation)

        # Check that the results were stored
        assert Phase.RETROSPECT in coordinator.results
        assert "evaluation" in coordinator.results[Phase.RETROSPECT]
        assert coordinator.results[Phase.RETROSPECT]["evaluation"] == evaluation

    def test_generate_report(self, coordinator, sample_task):
        """Test generating a report."""
        coordinator.start_cycle(sample_task)

        # Set up results for all phases
        coordinator.results = {
            Phase.EXPAND: {"completed": True, "approaches": []},
            Phase.DIFFERENTIATE: {"completed": True, "evaluation": {}},
            Phase.REFINE: {"completed": True, "implementation": {}},
            Phase.RETROSPECT: {"completed": True, "evaluation": {}, "is_valid": True}
        }

        # Generate the report
        report = coordinator.generate_report()

        # Check the report structure
        assert "task" in report
        assert "cycle_id" in report
        assert "timestamp" in report
        assert "phases" in report
        assert "summary" in report

        # Check that all phases are included
        assert "EXPAND" in report["phases"]
        assert "DIFFERENTIATE" in report["phases"]
        assert "REFINE" in report["phases"]
        assert "RETROSPECT" in report["phases"]

    def test_start_cycle_from_manifest(self, coordinator, sample_manifest):
        """Test starting an EDRR cycle from a manifest."""
        # Create a temporary manifest file
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = os.path.join(temp_dir, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(sample_manifest, f)

            # Start the cycle from the manifest
            coordinator.start_cycle_from_manifest(manifest_path)

            # Check that the manifest parser was initialized
            assert coordinator.manifest_parser is not None
            assert coordinator.current_phase == Phase.EXPAND
            assert coordinator.cycle_id is not None

    def test_enhanced_logging(self, enhanced_coordinator, sample_task):
        """Test enhanced logging functionality."""
        enhanced_coordinator.start_cycle(sample_task)

        # Set up results for all phases
        enhanced_coordinator.results = {
            Phase.EXPAND: {"completed": True, "approaches": []},
            Phase.DIFFERENTIATE: {"completed": True, "evaluation": {}},
            Phase.REFINE: {"completed": True, "implementation": {}},
            Phase.RETROSPECT: {"completed": True, "evaluation": {}, "is_valid": True}
        }

        # Progress through all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            enhanced_coordinator.progress_to_phase(phase)

        # Get execution traces
        traces = enhanced_coordinator.get_execution_traces()

        # Check trace structure
        assert "cycle_id" in traces
        assert "phases" in traces
        assert "overall_status" in traces
        assert "metadata" in traces

        # Check that all phases are included
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            assert phase.name in traces["phases"]
            phase_trace = traces["phases"][phase.name]
            assert "status" in phase_trace
            assert "start_time" in phase_trace
            assert "end_time" in phase_trace
            assert "metrics" in phase_trace

    def test_get_execution_history(self, enhanced_coordinator, sample_task):
        """Test getting execution history."""
        enhanced_coordinator.start_cycle(sample_task)

        # Progress through all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            enhanced_coordinator.progress_to_phase(phase)

        # Get execution history
        history = enhanced_coordinator.get_execution_history()

        # Check history structure
        assert len(history) >= 4  # At least one entry per phase
        for entry in history:
            assert "timestamp" in entry
            assert "phase" in entry
            assert "action" in entry
            assert "details" in entry

    def test_get_performance_metrics(self, enhanced_coordinator, sample_task):
        """Test getting performance metrics."""
        enhanced_coordinator.start_cycle(sample_task)

        # Progress through all phases
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            enhanced_coordinator.progress_to_phase(phase)

        # Get performance metrics
        metrics = enhanced_coordinator.get_performance_metrics()

        # Check metrics structure
        for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
            assert phase.name in metrics
            phase_metrics = metrics[phase.name]
            assert "duration" in phase_metrics
            assert "memory_usage" in phase_metrics
            assert "component_calls" in phase_metrics
