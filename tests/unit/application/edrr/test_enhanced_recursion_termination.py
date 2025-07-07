"""
Tests for enhanced recursion termination conditions in the EDRRCoordinator.

This module tests additional termination conditions for the should_terminate_recursion method:
1. Maximum recursion depth
2. Time-based termination
3. Memory usage
4. More robust historical effectiveness
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager


@pytest.fixture
def memory_manager():
    """Create a mock memory manager with historical patterns."""
    mock = MagicMock(spec=MemoryManager)
    # Set up retrieve_historical_patterns to return test patterns
    mock.retrieve_historical_patterns.return_value = [
        {"task_type": "refactoring", "recursion_effectiveness": 0.2},
        {"task_type": "testing", "recursion_effectiveness": 0.8},
        {"task_type": "documentation", "recursion_effectiveness": 0.6},
    ]
    return mock


@pytest.fixture
def coordinator(memory_manager):
    """Create an EDRRCoordinator instance with mocked dependencies."""
    wsde_team = MagicMock(spec=WSDETeam)
    code_analyzer = MagicMock(spec=CodeAnalyzer)
    ast_transformer = MagicMock(spec=AstTransformer)
    prompt_manager = MagicMock(spec=PromptManager)
    documentation_manager = MagicMock(spec=DocumentationManager)

    return EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
    )


def test_should_terminate_recursion_max_depth(coordinator):
    """Test that recursion terminates when maximum depth is reached."""
    # Set recursion depth to maximum allowed
    coordinator.recursion_depth = coordinator.max_recursion_depth

    # Create a task that would otherwise not trigger termination
    task = {
        "description": "Task at max depth",
        "granularity_score": 0.8,
        "cost_score": 0.2,
        "benefit_score": 0.9,
    }

    # Check if recursion should terminate
    should_terminate, reason = coordinator.should_terminate_recursion(task)

    # Verify that recursion terminates due to max depth
    assert should_terminate is True
    assert reason == "maximum recursion depth"


def test_should_terminate_recursion_time_based(coordinator):
    """Test that recursion terminates based on elapsed time."""
    # Start a cycle
    coordinator.start_cycle({"description": "Test Task"})

    # Set the cycle start time to be longer than the maximum allowed duration
    max_duration = coordinator.config.get("edrr", {}).get("recursion", {}).get("max_duration", 3600)
    coordinator._cycle_start_time = datetime.now() - timedelta(seconds=max_duration + 60)

    # Create a task that would otherwise not trigger termination
    task = {
        "description": "Long-running task",
        "granularity_score": 0.8,
        "cost_score": 0.2,
        "benefit_score": 0.9,
    }

    # Check if recursion should terminate
    should_terminate, reason = coordinator.should_terminate_recursion(task)

    # Verify that recursion terminates due to time limit
    assert should_terminate is True
    assert reason == "time limit exceeded"


def test_should_terminate_recursion_memory_usage(coordinator):
    """Test that recursion terminates based on memory usage."""
    # Start a cycle
    coordinator.start_cycle({"description": "Test Task"})

    # Create a task with high memory usage
    task = {
        "description": "Memory-intensive task",
        "memory_usage": 0.95,  # 95% of available memory
    }

    # Check if recursion should terminate
    should_terminate, reason = coordinator.should_terminate_recursion(task)

    # Verify that recursion terminates due to memory usage
    assert should_terminate is True
    assert reason == "memory usage limit"


def test_should_terminate_recursion_historical_effectiveness(coordinator):
    """Test that recursion terminates based on historical effectiveness."""
    # Start a cycle
    coordinator.start_cycle({"description": "Test Task"})

    # Create a task with a type that has historically been ineffective with recursion
    task = {
        "description": "Refactoring task",
        "type": "refactoring",
    }

    # Check if recursion should terminate
    should_terminate, reason = coordinator.should_terminate_recursion(task)

    # Verify that recursion terminates due to historical ineffectiveness
    assert should_terminate is True
    assert reason == "historical ineffectiveness"


def test_should_not_terminate_recursion_historical_effectiveness(coordinator):
    """Test that recursion continues for historically effective task types."""
    # Start a cycle
    coordinator.start_cycle({"description": "Test Task"})

    # Create a task with a type that has historically been effective with recursion
    task = {
        "description": "Testing task",
        "type": "testing",
    }

    # Check if recursion should terminate
    should_terminate, reason = coordinator.should_terminate_recursion(task)

    # Verify that recursion continues
    assert should_terminate is False
    assert reason is None


def test_should_terminate_recursion_combined_new_factors(coordinator):
    """Test that recursion terminates when multiple new factors are present."""
    # Set recursion depth close to maximum
    coordinator.recursion_depth = coordinator.max_recursion_depth - 1

    # Start a cycle
    coordinator.start_cycle({"description": "Test Task"})

    # Set the cycle start time to be close to the maximum allowed duration
    max_duration = coordinator.config.get("edrr", {}).get("recursion", {}).get("max_duration", 3600)
    coordinator._cycle_start_time = datetime.now() - timedelta(seconds=max_duration - 60)

    # Create a task with multiple factors
    task = {
        "description": "Complex task",
        "memory_usage": 0.85,  # 85% of available memory
        "type": "documentation",  # Moderately effective with recursion
        "granularity_score": 0.15,  # Low granularity (below threshold * 1.5)
        "quality_score": 0.8,  # High quality (approaching threshold)
        "resource_usage": 0.7,  # High resource usage (approaching limit)
    }

    # Check if recursion should terminate
    should_terminate, reason = coordinator.should_terminate_recursion(task)

    # Verify that recursion terminates due to one of the factors
    assert should_terminate is True
    assert reason in ["granularity threshold", "memory usage limit", "approaching memory limit", 
                     "approaching maximum recursion depth", "approaching time limit"]
