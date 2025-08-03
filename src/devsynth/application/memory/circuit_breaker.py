"""
Circuit Breaker implementation for memory operations.

This module provides a circuit breaker pattern implementation to prevent
cascading failures in cross-store memory operations.
"""

import time
import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from devsynth.logging_setup import DevSynthLogger

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Possible states of the circuit breaker."""
    CLOSED = "CLOSED"  # Normal operation, requests are allowed
    OPEN = "OPEN"      # Failure threshold exceeded, requests are blocked
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back to normal


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for memory operations.
    
    The circuit breaker pattern prevents cascading failures by stopping
    operations when a service is failing repeatedly. It allows the service
    time to recover before allowing operations again.
    
    Attributes:
        name: Name of the circuit breaker for identification
        failure_threshold: Number of failures before opening the circuit
        reset_timeout: Time in seconds before trying to close the circuit again
        state: Current state of the circuit breaker
        failure_count: Current count of consecutive failures
        last_failure_time: Timestamp of the last failure
        logger: Logger instance
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        reset_timeout: float = 60.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of the circuit breaker for identification
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Time in seconds before trying to close the circuit again
            logger: Optional logger instance
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.logger = logger or DevSynthLogger(__name__)
        
    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Exception: Any exception raised by the function
        """
        self._check_state()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
            
    def _check_state(self) -> None:
        """
        Check the current state of the circuit breaker.
        
        Raises:
            CircuitBreakerOpenError: If the circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            # Check if reset timeout has elapsed
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.logger.info(
                    f"Circuit breaker '{self.name}' transitioning from OPEN to HALF-OPEN"
                )
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                self.logger.warning(
                    f"Circuit breaker '{self.name}' is OPEN, rejecting request"
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open"
                )
                
    def _on_success(self) -> None:
        """Handle successful execution."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.logger.info(
                f"Circuit breaker '{self.name}' transitioning from HALF-OPEN to CLOSED"
            )
            self.state = CircuitBreakerState.CLOSED
            
        self.failure_count = 0
        
    def _on_failure(self, exception: Exception) -> None:
        """
        Handle failed execution.
        
        Args:
            exception: The exception that was raised
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if (self.state == CircuitBreakerState.CLOSED and 
                self.failure_count >= self.failure_threshold):
            self.logger.warning(
                f"Circuit breaker '{self.name}' transitioning from CLOSED to OPEN "
                f"after {self.failure_count} consecutive failures"
            )
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.logger.warning(
                f"Circuit breaker '{self.name}' transitioning from HALF-OPEN to OPEN "
                f"after a failure during test request"
            )
            self.state = CircuitBreakerState.OPEN
            
        self.logger.error(
            f"Circuit breaker '{self.name}' recorded failure: {exception}"
        )
        
    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.logger.info(f"Circuit breaker '{self.name}' has been reset")
        
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the circuit breaker.
        
        Returns:
            Dictionary with the current state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "reset_timeout": self.reset_timeout
        }


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    This class provides a centralized registry for creating and accessing
    circuit breakers by name.
    """
    
    def __init__(self):
        """Initialize the circuit breaker registry."""
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = DevSynthLogger(__name__)
        
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 3,
        reset_timeout: float = 60.0
    ) -> CircuitBreaker:
        """
        Get an existing circuit breaker or create a new one.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Time in seconds before trying to close the circuit again
            
        Returns:
            The circuit breaker instance
        """
        if name not in self._circuit_breakers:
            self.logger.info(f"Creating new circuit breaker: {name}")
            self._circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout,
                logger=self.logger
            )
            
        return self._circuit_breakers[name]
        
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get an existing circuit breaker by name.
        
        Args:
            name: Name of the circuit breaker
            
        Returns:
            The circuit breaker instance or None if not found
        """
        return self._circuit_breakers.get(name)
        
    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        for circuit_breaker in self._circuit_breakers.values():
            circuit_breaker.reset()
            
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current state of all circuit breakers.
        
        Returns:
            Dictionary mapping circuit breaker names to their states
        """
        return {
            name: circuit_breaker.get_state()
            for name, circuit_breaker in self._circuit_breakers.items()
        }


# Global circuit breaker registry
_circuit_breaker_registry = CircuitBreakerRegistry()

# Export the registry for direct import
circuit_breaker_registry = _circuit_breaker_registry


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """
    Get the global circuit breaker registry.
    
    Returns:
        The global circuit breaker registry
    """
    return _circuit_breaker_registry


def with_circuit_breaker(
    circuit_breaker_name: str,
    failure_threshold: int = 3,
    reset_timeout: float = 60.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for applying circuit breaker pattern to a function.
    
    Args:
        circuit_breaker_name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        reset_timeout: Time in seconds before trying to close the circuit again
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            registry = get_circuit_breaker_registry()
            circuit_breaker = registry.get_or_create(
                name=circuit_breaker_name,
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout
            )
            return circuit_breaker.execute(func, *args, **kwargs)
        return cast(Callable[..., T], wrapper)
    return decorator