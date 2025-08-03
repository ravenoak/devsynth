"""
Unit tests for the circuit breaker pattern implementation.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from devsynth.application.memory.circuit_breaker import CircuitBreaker, CircuitBreakerState, CircuitBreakerOpenError, CircuitBreakerRegistry, get_circuit_breaker_registry, with_circuit_breaker

@pytest.mark.medium
class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    @pytest.mark.medium
    def test_initialization(self):
        """Test that CircuitBreaker initializes with expected values."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=3, reset_timeout=60.0)
        assert circuit_breaker.name == 'test_breaker'
        assert circuit_breaker.failure_threshold == 3
        assert circuit_breaker.reset_timeout == 60.0
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time == 0.0

    @pytest.mark.medium
    def test_execute_success(self):
        """Test that execute succeeds when the function succeeds."""
        circuit_breaker = CircuitBreaker(name='test_breaker')
        mock_func = MagicMock(return_value='success')
        result = circuit_breaker.execute(mock_func, 'arg1', 'arg2', kwarg1='value1')
        mock_func.assert_called_once_with('arg1', 'arg2', kwarg1='value1')
        assert result == 'success'
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0

    @pytest.mark.medium
    def test_execute_failure(self):
        """Test that execute handles failure correctly."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=2)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.last_failure_time > 0

    @pytest.mark.medium
    def test_circuit_opens_after_threshold(self):
        """Test that the circuit opens after reaching the failure threshold."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=2)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 1
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == 2

    @pytest.mark.medium
    def test_open_circuit_rejects_requests(self):
        """Test that an open circuit rejects requests."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=1, reset_timeout=60.0)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.execute(mock_func)
        assert mock_func.call_count == 1

    @pytest.mark.medium
    def test_half_open_after_timeout(self):
        """Test that the circuit transitions to half-open after the reset timeout."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=1, reset_timeout=0.1)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        time.sleep(0.2)
        mock_success_func = MagicMock(return_value='success')
        result = circuit_breaker.execute(mock_success_func)
        mock_success_func.assert_called_once()
        assert result == 'success'
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0

    @pytest.mark.medium
    def test_half_open_to_open_on_failure(self):
        """Test that the circuit transitions from half-open to open on failure."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=1, reset_timeout=0.1)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        time.sleep(0.2)
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.medium
    def test_reset(self):
        """Test that reset returns the circuit breaker to closed state."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=1)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError, match='test error'):
            circuit_breaker.execute(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time == 0.0

    @pytest.mark.medium
    def test_get_state(self):
        """Test that get_state returns the expected state information."""
        circuit_breaker = CircuitBreaker(name='test_breaker', failure_threshold=3, reset_timeout=60.0)
        state = circuit_breaker.get_state()
        assert state['name'] == 'test_breaker'
        assert state['state'] == 'CLOSED'
        assert state['failure_count'] == 0
        assert state['failure_threshold'] == 3
        assert state['last_failure_time'] == 0.0
        assert state['reset_timeout'] == 60.0

@pytest.mark.medium
class TestCircuitBreakerRegistry:
    """Tests for the CircuitBreakerRegistry class."""

    @pytest.mark.medium
    def test_get_or_create(self):
        """Test that get_or_create returns a circuit breaker."""
        registry = CircuitBreakerRegistry()
        circuit_breaker = registry.get_or_create(name='test_breaker', failure_threshold=3, reset_timeout=60.0)
        assert circuit_breaker.name == 'test_breaker'
        assert circuit_breaker.failure_threshold == 3
        assert circuit_breaker.reset_timeout == 60.0
        same_circuit_breaker = registry.get_or_create(name='test_breaker')
        assert same_circuit_breaker is circuit_breaker

    @pytest.mark.medium
    def test_get(self):
        """Test that get returns an existing circuit breaker."""
        registry = CircuitBreakerRegistry()
        circuit_breaker = registry.get_or_create(name='test_breaker')
        same_circuit_breaker = registry.get(name='test_breaker')
        assert same_circuit_breaker is circuit_breaker
        non_existent = registry.get(name='non_existent')
        assert non_existent is None

    @pytest.mark.medium
    def test_reset_all(self):
        """Test that reset_all resets all circuit breakers."""
        registry = CircuitBreakerRegistry()
        breaker1 = registry.get_or_create(name='breaker1', failure_threshold=1)
        breaker2 = registry.get_or_create(name='breaker2', failure_threshold=1)
        mock_func = MagicMock(side_effect=ValueError('test error'))
        with pytest.raises(ValueError):
            breaker1.execute(mock_func)
        with pytest.raises(ValueError):
            breaker2.execute(mock_func)
        assert breaker1.state == CircuitBreakerState.OPEN
        assert breaker2.state == CircuitBreakerState.OPEN
        registry.reset_all()
        assert breaker1.state == CircuitBreakerState.CLOSED
        assert breaker2.state == CircuitBreakerState.CLOSED

    @pytest.mark.medium
    def test_get_all_states(self):
        """Test that get_all_states returns the expected state information."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create(name='breaker1')
        registry.get_or_create(name='breaker2')
        states = registry.get_all_states()
        assert 'breaker1' in states
        assert 'breaker2' in states
        assert states['breaker1']['state'] == 'CLOSED'
        assert states['breaker2']['state'] == 'CLOSED'

@pytest.mark.medium
class TestWithCircuitBreaker:
    """Tests for the with_circuit_breaker decorator."""

    @pytest.mark.medium
    def test_decorator(self):
        """Test that the decorator works correctly."""

        @pytest.mark.medium
        @with_circuit_breaker('test_decorator')
        def test_func(self, arg1, arg2=None):
            return f'{arg1}-{arg2}'
        result = test_func('value1', arg2='value2')
        assert result == 'value1-value2'
        registry = get_circuit_breaker_registry()
        circuit_breaker = registry.get('test_decorator')
        assert circuit_breaker is not None
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.medium
    def test_decorator_with_failure(self):
        """Test that the decorator handles failure correctly."""

        @with_circuit_breaker('test_failure', failure_threshold=1)
        def failing_func():
            raise ValueError('test error')
        with pytest.raises(ValueError, match='test error'):
            failing_func()
        registry = get_circuit_breaker_registry()
        circuit_breaker = registry.get('test_failure')
        assert circuit_breaker is not None
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        with pytest.raises(CircuitBreakerOpenError):
            failing_func()

@pytest.mark.medium
def test_global_registry():
    """Test that the global registry is a singleton."""
    registry1 = get_circuit_breaker_registry()
    registry2 = get_circuit_breaker_registry()
    assert registry1 is registry2