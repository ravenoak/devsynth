"""Unit tests for the EDRR Coordinator core functionality."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from devsynth.application.edrr.coordinator.core import (
    EDRRCoordinator,
    EDRRCoordinatorError,
)
from devsynth.exceptions import DevSynthError
from devsynth.methodology.base import Phase


class TestEDRRCoordinatorError:
    """Test EDRRCoordinatorError exception handling."""

    @pytest.mark.fast
    def test_error_basic_creation(self):
        """Test basic error creation without phase context."""
        error = EDRRCoordinatorError("Test error message")

        assert str(error) == "Test error message"
        assert error.error_code is None
        assert error.details == {}

    @pytest.mark.fast
    def test_error_with_phase_context(self):
        """Test error creation with phase context."""
        error = EDRRCoordinatorError(
            "Phase error", phase=Phase.EXPAND, error_code="PHASE_ERROR"
        )

        assert str(error) == "Phase error"
        assert error.error_code == "PHASE_ERROR"
        assert error.details["phase"] == "expand"

    @pytest.mark.fast
    def test_error_with_details(self):
        """Test error creation with additional details."""
        details = {"component": "test", "line": 42}
        error = EDRRCoordinatorError("Detailed error", details=details)

        assert error.details["component"] == "test"
        assert error.details["line"] == 42


class TestEDRRCoordinatorInitialization:
    """Test EDRRCoordinator initialization and basic setup."""

    @pytest.mark.fast
    def test_coordinator_initialization_defaults(self, tmp_project_dir):
        """Test coordinator initialization with default values."""
        with patch(
            "devsynth.application.edrr.coordinator.core.get_llm_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = {
                "edrr": {
                    "max_recursion_depth": 3,
                    "granularity_threshold": 0.2,
                }
            }

            coordinator = EDRRCoordinator()

            assert coordinator.max_recursion_depth == 3
            assert coordinator.granularity_threshold == 0.2
            assert coordinator.cost_benefit_ratio == 0.5
            assert coordinator.quality_threshold == 0.9
            assert coordinator.resource_limit == 0.8
            assert coordinator.complexity_threshold == 0.7
            assert coordinator.convergence_threshold == 0.85
            assert coordinator.diminishing_returns_threshold == 0.3
            assert coordinator.manual_phase_override is None
            assert coordinator.micro_cycle_hooks == {}
            assert coordinator.sync_hooks == []
            assert coordinator.recovery_hooks == {}

    @pytest.mark.fast
    def test_coordinator_initialization_custom_config(self, tmp_project_dir):
        """Test coordinator initialization with custom configuration."""
        custom_config = {
            "max_recursion_depth": 5,
            "granularity_threshold": 0.3,
            "cost_benefit_ratio": 0.6,
        }

        coordinator = EDRRCoordinator(custom_config)

        assert coordinator.max_recursion_depth == 5
        assert coordinator.granularity_threshold == 0.3
        assert coordinator.cost_benefit_ratio == 0.6

    @pytest.mark.fast
    def test_coordinator_dependencies_initialization(self, tmp_project_dir):
        """Test that coordinator initializes all dependencies correctly."""
        coordinator = EDRRCoordinator()

        # Check that all major components are initialized
        assert hasattr(coordinator, "memory_manager")
        assert hasattr(coordinator, "wsde_team_proxy")
        assert hasattr(coordinator, "code_analyzer")
        assert hasattr(coordinator, "prompt_manager")
        assert hasattr(coordinator, "documentation_manager")


class TestEDRRCoordinatorPhaseExecution:
    """Test EDRRCoordinator phase execution methods."""

    @pytest.mark.medium
    def test_start_cycle_basic(self, tmp_project_dir):
        """Test basic cycle execution."""
        coordinator = EDRRCoordinator()

        task = {
            "id": "test-task",
            "description": "Test task description",
            "requirements": "Test requirements",
        }

        # This would normally execute phases, but we'll mock the components
        with (
            patch.object(coordinator, "_execute_expand_phase") as mock_expand,
            patch.object(
                coordinator, "_execute_differentiate_phase"
            ) as mock_differentiate,
            patch.object(coordinator, "_execute_refine_phase") as mock_refine,
            patch.object(coordinator, "_execute_retrospect_phase") as mock_retrospect,
        ):

            # Mock successful phase execution
            mock_expand.return_value = {"status": "completed"}
            mock_differentiate.return_value = {"status": "completed"}
            mock_refine.return_value = {"status": "completed"}
            mock_retrospect.return_value = {"status": "completed"}

            coordinator.start_cycle(task)

            # Verify all phases were executed
            mock_expand.assert_called_once()
            mock_differentiate.assert_called_once()
            mock_refine.assert_called_once()
            mock_retrospect.assert_called_once()

    @pytest.mark.medium
    def test_start_cycle_with_error_handling(self, tmp_project_dir):
        """Test cycle execution with error handling."""
        coordinator = EDRRCoordinator()

        task = {"id": "error-task"}

        with patch.object(coordinator, "_execute_expand_phase") as mock_expand:
            # Mock phase failure
            mock_expand.side_effect = Exception("Phase failed")

            with pytest.raises(Exception) as exc_info:
                coordinator.start_cycle(task)

            assert "Phase failed" in str(exc_info.value)

    @pytest.mark.fast
    def test_start_cycle_from_manifest(self, tmp_project_dir):
        """Test cycle execution from manifest file."""
        coordinator = EDRRCoordinator()

        # Create a mock manifest file
        manifest_content = {
            "task": {"id": "manifest-task"},
            "phases": ["expand", "differentiate"],
        }

        with (
            patch("builtins.open", create=True) as mock_open,
            patch("yaml.safe_load") as mock_yaml_load,
            patch.object(coordinator, "start_cycle") as mock_start_cycle,
        ):

            mock_yaml_load.return_value = manifest_content

            # Mock the file opening
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.read.return_value = "test content"
            mock_open.return_value = mock_file

            coordinator.start_cycle_from_manifest("test_manifest.yml")

            mock_start_cycle.assert_called_once_with(manifest_content["task"])


class TestEDRRCoordinatorRecursion:
    """Test EDRRCoordinator recursion handling."""

    @pytest.mark.fast
    def test_should_terminate_recursion_depth_limit(self, tmp_project_dir):
        """Test recursion termination based on depth limit."""
        coordinator = EDRRCoordinator({"max_recursion_depth": 2})

        # Create a task that would exceed depth limit
        task = {"id": "deep-task", "recursion_depth": 3}  # Exceeds limit of 2

        should_terminate, reason = coordinator.should_terminate_recursion(task)

        assert should_terminate is True
        assert "maximum recursion depth" in reason

    @pytest.mark.fast
    def test_should_terminate_recursion_granularity(self, tmp_project_dir):
        """Test recursion termination based on granularity threshold."""
        coordinator = EDRRCoordinator()

        # Mock a task with low granularity score
        task = {
            "id": "low-granularity-task",
            "granularity_score": 0.1,  # Below default threshold of 0.2
        }

        should_terminate, reason = coordinator.should_terminate_recursion(task)

        assert should_terminate is True
        assert "granularity threshold" in reason

    @pytest.mark.fast
    def test_should_terminate_recursion_cost_benefit(self, tmp_project_dir):
        """Test recursion termination based on cost-benefit ratio."""
        coordinator = EDRRCoordinator()

        # Mock a task with poor cost-benefit ratio
        task = {
            "id": "poor-cost-benefit-task",
            "cost_benefit_ratio": 0.3,  # Below default threshold of 0.5
        }

        should_terminate, reason = coordinator.should_terminate_recursion(task)

        assert should_terminate is True
        assert "cost-benefit ratio" in reason

    @pytest.mark.fast
    def test_should_terminate_recursion_resource_limit(self, tmp_project_dir):
        """Test recursion termination based on resource limits."""
        coordinator = EDRRCoordinator()

        # Mock a task exceeding resource limits
        task = {
            "id": "resource-intensive-task",
            "resource_usage": 0.9,  # Above default limit of 0.8
        }

        should_terminate, reason = coordinator.should_terminate_recursion(task)

        assert should_terminate is True
        assert "resource limit" in reason

    @pytest.mark.fast
    def test_should_not_terminate_recursion_good_metrics(self, tmp_project_dir):
        """Test that recursion continues when metrics are good."""
        coordinator = EDRRCoordinator()

        # Mock a task with good metrics
        task = {
            "id": "good-task",
            "recursion_depth": 1,
            "granularity_score": 0.8,
            "cost_benefit_ratio": 0.9,
            "resource_usage": 0.3,
            "quality_score": 0.95,
            "complexity_score": 0.2,
            "convergence_score": 0.9,
            "diminishing_returns_score": 0.8,
        }

        should_terminate, reason = coordinator.should_terminate_recursion(task)

        assert should_terminate is False


class TestEDRRCoordinatorMicroCycles:
    """Test EDRRCoordinator micro-cycle functionality."""

    @pytest.mark.medium
    def test_create_micro_cycle(self, tmp_project_dir):
        """Test micro-cycle creation."""
        coordinator = EDRRCoordinator()

        parent_task = {"id": "parent-task"}
        subtask = {"id": "sub-task", "description": "Sub task"}

        with patch.object(coordinator, "_aggregate_with_parent") as mock_aggregate:
            micro_cycle = coordinator.create_micro_cycle(parent_task, subtask)

            assert micro_cycle is not None
            assert hasattr(micro_cycle, "parent_task")
            assert hasattr(micro_cycle, "subtask")
            mock_aggregate.assert_called_once()

    @pytest.mark.fast
    def test_register_micro_cycle_hook(self, tmp_project_dir):
        """Test micro-cycle hook registration."""
        coordinator = EDRRCoordinator()

        def test_hook(event, data):
            return f"processed-{event}"

        coordinator.register_micro_cycle_hook("test_event", test_hook)

        assert "test_event" in coordinator.micro_cycle_hooks
        assert coordinator.micro_cycle_hooks["test_event"] == test_hook

    @pytest.mark.fast
    def test_invoke_micro_cycle_hooks(self, tmp_project_dir):
        """Test micro-cycle hook invocation."""
        coordinator = EDRRCoordinator()

        hook_results = []

        def test_hook1(event, data):
            hook_results.append(f"hook1-{event}")
            return "result1"

        def test_hook2(event, data):
            hook_results.append(f"hook2-{event}")
            return "result2"

        coordinator.register_micro_cycle_hook("test_event", test_hook1)
        coordinator.register_micro_cycle_hook("test_event", test_hook2)

        result = coordinator._invoke_micro_cycle_hooks("test_event", {"test": "data"})

        assert len(hook_results) == 2
        assert "hook1-test_event" in hook_results
        assert "hook2-test_event" in hook_results
        assert len(result) == 2
        assert "result1" in result
        assert "result2" in result


class TestEDRRCoordinatorHooks:
    """Test EDRRCoordinator hook system."""

    @pytest.mark.fast
    def test_register_sync_hook(self, tmp_project_dir):
        """Test sync hook registration."""
        coordinator = EDRRCoordinator()

        def test_sync_hook(item):
            return f"sync-{item}"

        coordinator.register_sync_hook(test_sync_hook)

        assert len(coordinator.sync_hooks) == 1
        assert coordinator.sync_hooks[0] == test_sync_hook

    @pytest.mark.fast
    def test_invoke_sync_hooks(self, tmp_project_dir):
        """Test sync hook invocation."""
        coordinator = EDRRCoordinator()

        hook_calls = []

        def sync_hook1(item):
            hook_calls.append(f"sync1-{item}")

        def sync_hook2(item):
            hook_calls.append(f"sync2-{item}")

        coordinator.register_sync_hook(sync_hook1)
        coordinator.register_sync_hook(sync_hook2)

        coordinator._invoke_sync_hooks("test_item")

        assert len(hook_calls) == 2
        assert "sync1-test_item" in hook_calls
        assert "sync2-test_item" in hook_calls

    @pytest.mark.fast
    def test_register_recovery_hook(self, tmp_project_dir):
        """Test recovery hook registration."""
        coordinator = EDRRCoordinator()

        def recovery_hook(error, phase):
            return {"recovered": True}

        coordinator.register_recovery_hook(Phase.EXPAND, recovery_hook)

        assert Phase.EXPAND in coordinator.recovery_hooks
        assert coordinator.recovery_hooks[Phase.EXPAND] == recovery_hook

    @pytest.mark.fast
    def test_execute_recovery_hooks(self, tmp_project_dir):
        """Test recovery hook execution."""
        coordinator = EDRRCoordinator()

        hook_results = []

        def recovery_hook1(error, phase):
            hook_results.append(f"recovery1-{phase}")
            return {"action": "retry"}

        def recovery_hook2(error, phase):
            hook_results.append(f"recovery2-{phase}")
            return {"action": "fallback"}

        coordinator.register_recovery_hook(Phase.EXPAND, recovery_hook1)
        coordinator.register_recovery_hook(Phase.EXPAND, recovery_hook2)

        test_error = Exception("Test error")
        results = coordinator._execute_recovery_hooks(test_error, Phase.EXPAND)

        assert len(hook_results) == 2
        assert "recovery1-expand" in hook_results
        assert "recovery2-expand" in hook_results
        assert len(results) == 2
        assert {"action": "retry"} in results
        assert {"action": "fallback"} in results


class TestEDRRCoordinatorPhaseManagement:
    """Test EDRRCoordinator phase management."""

    @pytest.mark.fast
    def test_set_manual_phase_override(self, tmp_project_dir):
        """Test manual phase override setting."""
        coordinator = EDRRCoordinator()

        coordinator.set_manual_phase_override(Phase.REFINE)

        assert coordinator.manual_phase_override == Phase.REFINE

        coordinator.set_manual_phase_override(None)

        assert coordinator.manual_phase_override is None

    @pytest.mark.fast
    def test_get_phase_quality_threshold(self, tmp_project_dir):
        """Test phase quality threshold retrieval."""
        coordinator = EDRRCoordinator()

        # Test default threshold
        threshold = coordinator._get_phase_quality_threshold(Phase.EXPAND)
        assert threshold == 0.9  # Default quality threshold

        # Test custom threshold per phase
        coordinator.phase_quality_thresholds = {Phase.EXPAND: 0.8}
        threshold = coordinator._get_phase_quality_threshold(Phase.EXPAND)
        assert threshold == 0.8


class TestEDRRCoordinatorUtilityMethods:
    """Test EDRRCoordinator utility methods."""

    @pytest.mark.fast
    def test_sanitize_positive_int(self, tmp_project_dir):
        """Test positive integer sanitization."""
        coordinator = EDRRCoordinator()

        # Test valid input
        result = coordinator._sanitize_positive_int(5, default=3)
        assert result == 5

        # Test invalid input (negative)
        result = coordinator._sanitize_positive_int(-1, default=3)
        assert result == 3

        # Test invalid input (zero)
        result = coordinator._sanitize_positive_int(0, default=3)
        assert result == 3

        # Test string input
        result = coordinator._sanitize_positive_int("invalid", default=3)
        assert result == 3

        # Test max value constraint
        result = coordinator._sanitize_positive_int(15, default=3, max_value=10)
        assert result == 10

    @pytest.mark.fast
    def test_sanitize_threshold(self, tmp_project_dir):
        """Test threshold sanitization."""
        coordinator = EDRRCoordinator()

        # Test valid threshold
        result = coordinator._sanitize_threshold(0.7, default=0.5)
        assert result == 0.7

        # Test invalid threshold (too high)
        result = coordinator._sanitize_threshold(1.5, default=0.5)
        assert result == 0.5

        # Test invalid threshold (too low)
        result = coordinator._sanitize_threshold(-0.1, default=0.5)
        assert result == 0.5

        # Test string input
        result = coordinator._sanitize_threshold("invalid", default=0.5)
        assert result == 0.5


class TestEDRRCoordinatorIntegration:
    """Test EDRRCoordinator integration scenarios."""

    @pytest.mark.slow
    def test_full_edrr_cycle_execution(self, tmp_project_dir):
        """Test complete EDRR cycle execution."""
        coordinator = EDRRCoordinator()

        task = {
            "id": "integration-test",
            "description": "Full EDRR cycle test",
            "requirements": "Test all phases",
        }

        # Mock all phase executions
        with (
            patch.object(coordinator, "_execute_expand_phase") as mock_expand,
            patch.object(
                coordinator, "_execute_differentiate_phase"
            ) as mock_differentiate,
            patch.object(coordinator, "_execute_refine_phase") as mock_refine,
            patch.object(coordinator, "_execute_retrospect_phase") as mock_retrospect,
        ):

            # Configure mocks to return successful results
            for mock_phase in [
                mock_expand,
                mock_differentiate,
                mock_refine,
                mock_retrospect,
            ]:
                mock_phase.return_value = {
                    "status": "completed",
                    "phase": mock_phase._mock_name.split("_")[-1].replace("mock_", ""),
                }

            # Execute the cycle
            coordinator.start_cycle(task)

            # Verify all phases were called
            mock_expand.assert_called_once()
            mock_differentiate.assert_called_once()
            mock_refine.assert_called_once()
            mock_retrospect.assert_called_once()

    @pytest.mark.medium
    def test_edrr_cycle_with_micro_cycles(self, tmp_project_dir):
        """Test EDRR cycle with micro-cycle creation."""
        coordinator = EDRRCoordinator()

        task = {
            "id": "micro-cycle-test",
            "create_micro_cycles": True,
            "micro_cycle_config": {"count": 2},
        }

        with (
            patch.object(coordinator, "_execute_expand_phase") as mock_expand,
            patch.object(
                coordinator, "_maybe_create_micro_cycles"
            ) as mock_micro_cycles,
        ):

            mock_expand.return_value = {"status": "completed"}
            mock_micro_cycles.return_value = None

            coordinator.start_cycle(task)

            mock_expand.assert_called_once()
            mock_micro_cycles.assert_called_once()

    @pytest.mark.fast
    def test_edrr_cycle_error_recovery(self, tmp_project_dir):
        """Test EDRR cycle with error recovery."""
        coordinator = EDRRCoordinator()

        def recovery_hook(error, phase):
            return {"recovered": True, "fallback": "use_default"}

        coordinator.register_recovery_hook(Phase.EXPAND, recovery_hook)

        task = {"id": "recovery-test"}

        with patch.object(coordinator, "_execute_expand_phase") as mock_expand:
            # First call fails, second succeeds after recovery
            mock_expand.side_effect = [
                Exception("Initial failure"),
                {"status": "recovered"},
            ]

            # Should complete successfully after recovery
            coordinator.start_cycle(task)

            assert mock_expand.call_count == 2
