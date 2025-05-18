
"""
Fallback mechanisms for graceful degradation in the DevSynth system.

This module provides utilities for implementing graceful degradation with fallback
mechanisms for critical components, ensuring that the system can continue to function
even when errors occur.
"""

import time
import random
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

from .exceptions import DevSynthError
from .logging_setup import DevSynthLogger

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Create a logger for this module
logger = DevSynthLogger("fallback")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Exception, ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)
        exponential_base: Base for the exponential backoff (default: 2.0)
        jitter: Whether to add random jitter to the delay (default: True)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        retryable_exceptions: Tuple of exceptions that should trigger a retry (default: (Exception,))
        on_retry: Optional callback function to call on each retry attempt
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Initialize variables
            num_retries = 0
            delay = initial_delay
            
            # Loop until max retries reached
            while True:
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    num_retries += 1
                    if num_retries > max_retries:
                        logger.error(
                            f"Maximum retry attempts ({max_retries}) exceeded",
                            error=e,
                            function=func.__name__,
                            max_retries=max_retries
                        )
                        raise
                    
                    # Calculate delay with jitter if enabled
                    if jitter:
                        delay = min(max_delay, delay * exponential_base * (0.5 + random.random()))
                    else:
                        delay = min(max_delay, delay * exponential_base)
                    
                    # Log retry attempt
                    logger.warning(
                        f"Retry attempt {num_retries}/{max_retries} after {delay:.2f}s delay",
                        error=e,
                        function=func.__name__,
                        retry_attempt=num_retries,
                        max_retries=max_retries,
                        delay=delay
                    )
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, num_retries, delay)
                        except Exception as callback_error:
                            logger.warning(
                                f"Error in on_retry callback: {str(callback_error)}",
                                error=callback_error
                            )
                    
                    # Wait before retrying
                    time.sleep(delay)
        
        return wrapper
    
    return decorator


def with_fallback(
    fallback_function: Callable[..., R],
    exceptions_to_catch: Tuple[Exception, ...] = (Exception,),
    should_fallback: Optional[Callable[[Exception], bool]] = None,
    log_original_error: bool = True
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for providing a fallback function when the primary function fails.
    
    Args:
        fallback_function: The fallback function to call when the primary function fails
        exceptions_to_catch: Tuple of exceptions that should trigger the fallback (default: (Exception,))
        should_fallback: Optional function to determine if fallback should be used for a given exception
        log_original_error: Whether to log the original error (default: True)
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            try:
                return func(*args, **kwargs)
            except exceptions_to_catch as e:
                # Check if we should use the fallback
                if should_fallback and not should_fallback(e):
                    raise
                
                # Log the original error
                if log_original_error:
                    logger.warning(
                        f"Using fallback for {func.__name__} due to error: {str(e)}",
                        error=e,
                        function=func.__name__,
                        fallback_function=fallback_function.__name__
                    )
                
                # Call the fallback function
                return fallback_function(*args, **kwargs)
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, all calls pass through
    - OPEN: Failure threshold exceeded, all calls fail fast
    - HALF_OPEN: After a timeout, allows a limited number of test calls
    """
    
    # Circuit breaker states
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        test_calls: int = 1,
        exception_types: Tuple[Exception, ...] = (Exception,)
    ):
        """
        Initialize a circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening the circuit (default: 5)
            recovery_timeout: Time in seconds before attempting recovery (default: 60.0)
            test_calls: Number of test calls allowed in HALF_OPEN state (default: 1)
            exception_types: Types of exceptions that count as failures (default: (Exception,))
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.test_calls = test_calls
        self.exception_types = exception_types
        
        # State variables
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.test_calls_remaining = 0
        
        # Create a logger
        self.logger = DevSynthLogger("circuit_breaker")
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for applying the circuit breaker pattern to a function.
        
        Args:
            func: The function to protect with the circuit breaker
            
        Returns:
            A wrapped function with circuit breaker protection
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(func, *args, **kwargs)
        
        return wrapper
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call a function with circuit breaker protection.
        
        Args:
            func: The function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function call
            
        Raises:
            DevSynthError: If the circuit is open
        """
        # Check if the circuit is open
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                # Transition to half-open state
                self.state = self.HALF_OPEN
                self.test_calls_remaining = self.test_calls
                self.logger.info(
                    f"Circuit breaker for {func.__name__} transitioned from OPEN to HALF_OPEN",
                    function=func.__name__,
                    state=self.state
                )
            else:
                # Circuit is still open, fail fast
                self.logger.warning(
                    f"Circuit breaker for {func.__name__} is OPEN, failing fast",
                    function=func.__name__,
                    state=self.state,
                    recovery_time_remaining=self.recovery_timeout - (time.time() - self.last_failure_time)
                )
                raise DevSynthError(
                    f"Circuit breaker for {func.__name__} is open",
                    error_code="CIRCUIT_OPEN",
                    details={
                        "function": func.__name__,
                        "recovery_time_remaining": self.recovery_timeout - (time.time() - self.last_failure_time)
                    }
                )
        
        # Call the function
        try:
            result = func(*args, **kwargs)
            
            # If the call succeeded and we're in half-open state
            if self.state == self.HALF_OPEN:
                self.test_calls_remaining -= 1
                
                # If all test calls succeeded, close the circuit
                if self.test_calls_remaining <= 0:
                    self.state = self.CLOSED
                    self.failure_count = 0
                    self.logger.info(
                        f"Circuit breaker for {func.__name__} transitioned from HALF_OPEN to CLOSED",
                        function=func.__name__,
                        state=self.state
                    )
            
            return result
        except self.exception_types as e:
            # Record the failure
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # If we're in half-open state or we've reached the failure threshold
            if self.state == self.HALF_OPEN or (self.state == self.CLOSED and self.failure_count >= self.failure_threshold):
                # Open the circuit
                self.state = self.OPEN
                self.logger.warning(
                    f"Circuit breaker for {func.__name__} transitioned to OPEN due to failure",
                    error=e,
                    function=func.__name__,
                    state=self.state,
                    failure_count=self.failure_count
                )
            
            # Re-raise the exception
            raise
    
    def reset(self) -> None:
        """Reset the circuit breaker to its initial state."""
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.test_calls_remaining = 0
        self.logger.info("Circuit breaker reset to initial state")


class Bulkhead:
    """
    Bulkhead pattern implementation for isolating failures.
    
    The bulkhead pattern limits the number of concurrent executions of a function
    to prevent resource exhaustion and isolate failures.
    """
    
    def __init__(self, max_concurrent_calls: int = 10, max_queue_size: int = 5):
        """
        Initialize a bulkhead.
        
        Args:
            max_concurrent_calls: Maximum number of concurrent calls allowed (default: 10)
            max_queue_size: Maximum size of the waiting queue (default: 5)
        """
        self.max_concurrent_calls = max_concurrent_calls
        self.max_queue_size = max_queue_size
        
        # State variables
        self.current_calls = 0
        self.queue_size = 0
        
        # Create a logger
        self.logger = DevSynthLogger("bulkhead")
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for applying the bulkhead pattern to a function.
        
        Args:
            func: The function to protect with the bulkhead
            
        Returns:
            A wrapped function with bulkhead protection
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(func, *args, **kwargs)
        
        return wrapper
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call a function with bulkhead protection.
        
        Args:
            func: The function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function call
            
        Raises:
            DevSynthError: If the bulkhead is full
        """
        # Check if we can execute the call
        if self.current_calls >= self.max_concurrent_calls:
            # Check if we can queue the call
            if self.queue_size >= self.max_queue_size:
                # Bulkhead is full, reject the call
                self.logger.warning(
                    f"Bulkhead for {func.__name__} is full, rejecting call",
                    function=func.__name__,
                    current_calls=self.current_calls,
                    queue_size=self.queue_size
                )
                raise DevSynthError(
                    f"Bulkhead for {func.__name__} is full",
                    error_code="BULKHEAD_FULL",
                    details={
                        "function": func.__name__,
                        "current_calls": self.current_calls,
                        "queue_size": self.queue_size
                    }
                )
            
            # Queue the call
            self.queue_size += 1
            self.logger.debug(
                f"Queuing call to {func.__name__}",
                function=func.__name__,
                current_calls=self.current_calls,
                queue_size=self.queue_size
            )
            
            # Wait for a slot to become available
            while self.current_calls >= self.max_concurrent_calls:
                time.sleep(0.1)
            
            # Dequeue the call
            self.queue_size -= 1
        
        # Execute the call
        self.current_calls += 1
        self.logger.debug(
            f"Executing call to {func.__name__}",
            function=func.__name__,
            current_calls=self.current_calls,
            queue_size=self.queue_size
        )
        
        try:
            return func(*args, **kwargs)
        finally:
            # Release the slot
            self.current_calls -= 1
            self.logger.debug(
                f"Completed call to {func.__name__}",
                function=func.__name__,
                current_calls=self.current_calls,
                queue_size=self.queue_size
            )
