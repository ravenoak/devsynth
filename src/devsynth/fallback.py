"""
Fallback mechanisms for graceful degradation in the DevSynth system.

This module provides utilities for implementing graceful degradation with fallback
mechanisms for critical components, ensuring that the system can continue to function
even when errors occur.
"""

import time
import random
import functools
import threading
import queue
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

from .exceptions import DevSynthError
from .logging_setup import DevSynthLogger
from .metrics import inc_retry

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")

# Create a logger for this module
logger = DevSynthLogger("fallback")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Exception, ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    should_retry: Optional[Callable[[Exception], bool]] = None,
    retry_conditions: Optional[List[Callable[[Exception], bool]]] = None,
    retry_on_result: Optional[Callable[[T], bool]] = None,
    track_metrics: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying a function with exponential backoff.

    Parameters
    ----------
    max_retries : int
        Maximum number of retry attempts (default: 3)
    initial_delay : float
        Initial delay between retries in seconds (default: 1.0)
    exponential_base : float
        Base for the exponential backoff (default: 2.0)
    jitter : bool
        Whether to add random jitter to the delay (default: True)
    max_delay : float
        Maximum delay between retries in seconds (default: 60.0)
    retryable_exceptions : Tuple[Exception, ...]
        Tuple of exceptions that should trigger a retry (default: (Exception,))
    on_retry : Optional[Callable[[Exception, int, float], None]]
        Optional callback function to call on each retry attempt
    should_retry : Optional[Callable[[Exception], bool]]
        Optional function that determines if a caught exception should trigger
        another retry. If it returns ``False`` the exception is re-raised.
    retry_conditions : Optional[List[Callable[[Exception], bool]]]
        Additional per-exception conditions that must all evaluate to ``True``
        for the retry to continue. If any condition returns ``False`` the
        exception is re-raised.

    Returns
    -------
    Callable
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
                    result = func(*args, **kwargs)
                    if retry_on_result and retry_on_result(result):
                        raise ValueError("retry_on_result triggered")
                    if track_metrics:
                        inc_retry("success")
                    return result
                except ValueError as e:
                    if str(e) == "retry_on_result triggered":
                        num_retries += 1
                        if num_retries > max_retries:
                            if track_metrics:
                                inc_retry("failure")
                            raise
                        if track_metrics:
                            inc_retry("invalid")
                        if jitter:
                            delay = min(
                                max_delay,
                                delay * exponential_base * (0.5 + random.random()),
                            )
                        else:
                            delay = min(max_delay, delay * exponential_base)
                        logger.warning(
                            f"Retrying due to invalid result {num_retries}/{max_retries} after {delay:.2f}s",
                            function=func.__name__,
                            retry_attempt=num_retries,
                            delay=delay,
                        )
                        time.sleep(delay)
                        continue
                    raise
                except retryable_exceptions as e:
                    if should_retry and not should_retry(e):
                        logger.warning(
                            f"Not retrying {func.__name__} due to should_retry policy",
                            error=e,
                            function=func.__name__,
                        )
                        if track_metrics:
                            inc_retry("abort")
                        raise
                    if retry_conditions and not all(
                        cond(e) for cond in retry_conditions
                    ):
                        logger.warning(
                            f"Not retrying {func.__name__} due to retry_conditions policy",
                            error=e,
                            function=func.__name__,
                        )
                        if track_metrics:
                            inc_retry("abort")
                        raise

                    num_retries += 1
                    if num_retries > max_retries:
                        logger.error(
                            f"Maximum retry attempts ({max_retries}) exceeded",
                            error=e,
                            function=func.__name__,
                            max_retries=max_retries,
                        )
                        if track_metrics:
                            inc_retry("failure")
                        raise

                    # Calculate delay with jitter if enabled
                    if jitter:
                        delay = min(
                            max_delay,
                            delay * exponential_base * (0.5 + random.random()),
                        )
                    else:
                        delay = min(max_delay, delay * exponential_base)

                    # Log retry attempt
                    logger.warning(
                        f"Retry attempt {num_retries}/{max_retries} after {delay:.2f}s delay",
                        error=e,
                        function=func.__name__,
                        retry_attempt=num_retries,
                        max_retries=max_retries,
                        delay=delay,
                    )
                    if track_metrics:
                        inc_retry("attempt")

                    # Call on_retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, num_retries, delay)
                        except Exception as callback_error:
                            logger.warning(
                                f"Error in on_retry callback: {str(callback_error)}",
                                error=callback_error,
                            )

                    # Wait before retrying
                    time.sleep(delay)

        return wrapper

    return decorator


def with_fallback(
    fallback_function: Callable[..., R],
    exceptions_to_catch: Tuple[Exception, ...] = (Exception,),
    should_fallback: Optional[Callable[[Exception], bool]] = None,
    log_original_error: bool = True,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for providing a fallback function when the primary function fails.

    Parameters
    ----------
    fallback_function : Callable
        The fallback function to call when the primary function fails
    exceptions_to_catch : Tuple[Exception, ...]
        Tuple of exceptions that should trigger the fallback (default: (Exception,))
    should_fallback : Optional[Callable[[Exception], bool]]
        Optional function to determine if fallback should be used for a given exception
    log_original_error : bool
        Whether to log the original error (default: True)

    Returns
    -------
    Callable
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
                        fallback_function=fallback_function.__name__,
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
        exception_types: Tuple[Exception, ...] = (Exception,),
    ):
        """
        Initialize a circuit breaker.

        Parameters
        ----------
        failure_threshold : int
            Number of failures before opening the circuit (default: 5)
        recovery_timeout : float
            Time in seconds before attempting recovery (default: 60.0)
        test_calls : int
            Number of test calls allowed in HALF_OPEN state (default: 1)
        exception_types : Tuple[Exception, ...]
            Types of exceptions that count as failures (default: (Exception,))
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

        # Lock for thread-safe state transitions
        self.lock = threading.Lock()

        # Create a logger
        self.logger = DevSynthLogger("circuit_breaker")

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for applying the circuit breaker pattern to a function.

        Parameters
        ----------
        func : Callable
            The function to protect with the circuit breaker

        Returns
        -------
        Callable
            A wrapped function with circuit breaker protection
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call a function with circuit breaker protection.

        Parameters
        ----------
        func : Callable
            The function to call
        *args: Any
            Positional arguments for the function
        **kwargs: Any
            Keyword arguments for the function

        Returns
        -------
        Any
            The result of the function call

        Raises
        ------
        DevSynthError
            If the circuit is open
        """
        # Check if the circuit is open
        with self.lock:
            state = self.state
            last_failure_time = self.last_failure_time
        if state == self.OPEN:
            if time.time() - last_failure_time >= self.recovery_timeout:
                with self.lock:
                    self.state = self.HALF_OPEN
                    self.test_calls_remaining = self.test_calls
                self.logger.info(
                    f"Circuit breaker for {func.__name__} transitioned from OPEN to HALF_OPEN",
                    function=func.__name__,
                    state=self.state,
                )
            else:
                self.logger.warning(
                    f"Circuit breaker for {func.__name__} is OPEN, failing fast",
                    function=func.__name__,
                    state=state,
                    recovery_time_remaining=self.recovery_timeout
                    - (time.time() - last_failure_time),
                )
                raise DevSynthError(
                    f"Circuit breaker for {func.__name__} is open",
                    error_code="CIRCUIT_OPEN",
                    details={
                        "function": func.__name__,
                        "recovery_time_remaining": self.recovery_timeout
                        - (time.time() - last_failure_time),
                    },
                )

        # Call the function
        try:
            result = func(*args, **kwargs)

            with self.lock:
                if self.state == self.HALF_OPEN:
                    self.test_calls_remaining -= 1
                    if self.test_calls_remaining <= 0:
                        self.state = self.CLOSED
                        self.failure_count = 0
                        self.logger.info(
                            f"Circuit breaker for {func.__name__} transitioned from HALF_OPEN to CLOSED",
                            function=func.__name__,
                            state=self.state,
                        )

            return result
        except self.exception_types as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.state == self.HALF_OPEN or (
                    self.state == self.CLOSED
                    and self.failure_count >= self.failure_threshold
                ):
                    self.state = self.OPEN
                    self.logger.warning(
                        f"Circuit breaker for {func.__name__} transitioned to OPEN due to failure",
                        error=e,
                        function=func.__name__,
                        state=self.state,
                        failure_count=self.failure_count,
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

        Parameters
        ----------
        max_concurrent_calls : int
            Maximum number of concurrent calls allowed (default: 10)
        max_queue_size : int
            Maximum size of the waiting queue (default: 5)
        """
        self.max_concurrent_calls = max_concurrent_calls
        self.max_queue_size = max_queue_size

        # Thread-safe counters and primitives
        self._semaphore = threading.Semaphore(self.max_concurrent_calls)
        self.lock = threading.Lock()
        self.current_calls = 0
        self.queue_size = 0

        # Create a logger
        self.logger = DevSynthLogger("bulkhead")

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for applying the bulkhead pattern to a function.

        Parameters
        ----------
        func : Callable
            The function to protect with the bulkhead

        Returns
        -------
        Callable
            A wrapped function with bulkhead protection
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call a function with bulkhead protection.

        Parameters
        ----------
        func : Callable
            The function to call
        *args: Any
            Positional arguments for the function
        **kwargs: Any
            Keyword arguments for the function

        Returns
        -------
        Any
            The result of the function call

        Raises
        ------
        DevSynthError
            If the bulkhead is full
        """
        if not self._semaphore.acquire(blocking=False):
            with self.lock:
                if self.queue_size >= self.max_queue_size:
                    self.logger.warning(
                        f"Bulkhead for {func.__name__} is full, rejecting call",
                        function=func.__name__,
                        current_calls=self.current_calls,
                        queue_size=self.queue_size,
                    )
                    raise DevSynthError(
                        f"Bulkhead for {func.__name__} is full",
                        error_code="BULKHEAD_FULL",
                        details={
                            "function": func.__name__,
                            "current_calls": self.current_calls,
                            "queue_size": self.queue_size,
                        },
                    )
                self.queue_size += 1
            self.logger.debug(
                f"Queuing call to {func.__name__}",
                function=func.__name__,
                current_calls=self.current_calls,
                queue_size=self.queue_size,
            )
            self._semaphore.acquire()
            with self.lock:
                self.queue_size -= 1

        with self.lock:
            self.current_calls += 1
        self.logger.debug(
            f"Executing call to {func.__name__}",
            function=func.__name__,
            current_calls=self.current_calls,
            queue_size=self.queue_size,
        )

        try:
            return func(*args, **kwargs)
        finally:
            with self.lock:
                self.current_calls -= 1
            self._semaphore.release()
