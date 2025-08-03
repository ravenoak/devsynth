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
    mock.retrieve_historical_patterns.return_value = [{'task_type': 'refactoring', 'recursion_effectiveness': 0.2}, {'task_type': 'test', 'recursion_effectiveness': 0.3}, {'task_type': 'testing', 'recursion_effectiveness': 0.8}, {'task_type': 'documentation', 'recursion_effectiveness': 0.6}]
    return mock

@pytest.fixture
def coordinator(memory_manager):
    """Create an EDRRCoordinator instance with mocked dependencies."""
    wsde_team = MagicMock(spec=WSDETeam)
    code_analyzer = MagicMock(spec=CodeAnalyzer)
    ast_transformer = MagicMock(spec=AstTransformer)
    prompt_manager = MagicMock(spec=PromptManager)
    documentation_manager = MagicMock(spec=DocumentationManager)
    return EDRRCoordinator(memory_manager=memory_manager, wsde_team=wsde_team, code_analyzer=code_analyzer, ast_transformer=ast_transformer, prompt_manager=prompt_manager, documentation_manager=documentation_manager, enable_enhanced_logging=True)

@pytest.mark.medium
def test_should_terminate_recursion_max_depth_succeeds(coordinator):
    """Test that recursion terminates when maximum depth is reached.

ReqID: N/A"""
    coordinator.recursion_depth = coordinator.max_recursion_depth
    task = {'description': 'Task at max depth', 'granularity_score': 0.8, 'cost_score': 0.2, 'benefit_score': 0.9}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is True
    assert 'max_depth' in reason

@pytest.mark.medium
def test_should_terminate_recursion_time_based_succeeds(coordinator):
    """Test that recursion terminates based on elapsed time.

ReqID: N/A"""
    coordinator.start_cycle({'description': 'Test Task'})
    max_duration = coordinator.config.get('edrr', {}).get('recursion', {}).get('max_duration', 3600)
    coordinator._cycle_start_time = datetime.now() - timedelta(seconds=max_duration + 60)
    task = {'description': 'Long-running task', 'granularity_score': 0.8, 'cost_score': 0.2, 'benefit_score': 0.9}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is True
    assert 'time_limit' in reason

@pytest.mark.medium
def test_should_terminate_recursion_memory_usage_succeeds(coordinator):
    """Test that recursion terminates based on memory usage.

ReqID: N/A"""
    coordinator.start_cycle({'description': 'Test Task'})
    task = {'description': 'Memory-intensive task', 'memory_usage': 0.95}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is True
    assert 'memory_limit' in reason

@pytest.mark.medium
def test_should_terminate_recursion_historical_effectiveness_succeeds(coordinator):
    """Test that recursion terminates based on historical effectiveness.

ReqID: N/A"""
    coordinator.start_cycle({'description': 'Test Task'})
    task = {'description': 'Test task', 'type': 'test'}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is True
    assert 'historical' in reason

@pytest.mark.medium
def test_should_not_terminate_recursion_historical_effectiveness_succeeds(coordinator):
    """Test that recursion continues for historically effective task types.

ReqID: N/A"""
    coordinator.start_cycle({'description': 'Test Task'})
    task = {'description': 'Testing task', 'type': 'testing'}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is False
    assert reason is None

@pytest.mark.medium
def test_should_terminate_recursion_combined_new_factors_succeeds(coordinator):
    """Test that recursion terminates when multiple new factors are present.

ReqID: N/A"""
    coordinator.recursion_depth = coordinator.max_recursion_depth - 1
    coordinator.start_cycle({'description': 'Test Task'})
    max_duration = coordinator.config.get('edrr', {}).get('recursion', {}).get('max_duration', 3600)
    coordinator._cycle_start_time = datetime.now() - timedelta(seconds=max_duration - 60)
    task = {'description': 'Complex task', 'memory_usage': 0.85, 'type': 'documentation', 'granularity_score': 0.15, 'quality_score': 0.8, 'resource_usage': 0.7}
    should_terminate, reason = coordinator.should_terminate_recursion(task)
    assert should_terminate is True
    assert reason in ['granularity threshold', 'memory usage limit', 'approaching memory limit', 'approaching maximum recursion depth', 'approaching time limit']