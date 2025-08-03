"""
Retry mechanism for memory operations.

This module provides a retry mechanism with exponential backoff for memory operations
to handle transient failures and improve reliability of cross-store operations.
"""

import time
import random
import logging
from functools import wraps
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, cast

from devsynth.logging_setup import DevSynthLogger

T = TypeVar('T')


class RetryError(Exception):
    """Exception raised when all retry attempts fail."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        """
        Initialize the retry error.
        
        Args:
            message: Error message
            last_exception: The last exception that was caught during retry
        """
        super().__init__(message)
        self.last_exception = last_exception


def retry_with_backoff(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_backoff: float = 60.0,
    jitter: bool = True,
    exceptions_to_retry: Optional[List[Type[Exception]]] = None,
    logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for backoff time after each retry
        max_backoff: Maximum backoff time in seconds
        jitter: Whether to add random jitter to backoff time
        exceptions_to_retry: List of exception types to retry on (defaults to all exceptions)
        logger: Optional logger instance
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            logger = logger or DevSynthLogger(__name__)
            
            retry_count = 0
            backoff = initial_backoff
            last_exception = None
            
            while retry_count <= max_retries:
                try:
                    if retry_count > 0:
                        logger.info(
                            f"Retry attempt {retry_count}/{max_retries} for {func.__name__}"
                        )
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if we should retry this exception
                    if (exceptions_to_retry is not None and 
                            not any(isinstance(e, exc) for exc in exceptions_to_retry)):
                        logger.warning(
                            f"Exception {type(e).__name__} not in retry list, re-raising"
                        )
                        raise
                    
                    last_exception = e
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        break
                    
                    # Calculate backoff time with jitter
                    actual_backoff = min(backoff, max_backoff)
                    if jitter:
                        # Add random jitter between 0% and 25%
                        jitter_amount = random.uniform(0, 0.25 * actual_backoff)
                        actual_backoff += jitter_amount
                    
                    logger.warning(
                        f"Attempt {retry_count} failed with {type(e).__name__}: {e}. "
                        f"Retrying in {actual_backoff:.2f} seconds..."
                    )
                    
                    # Wait before retrying
                    time.sleep(actual_backoff)
                    
                    # Increase backoff for next attempt
                    backoff *= backoff_multiplier
            
            # If we get here, all retries failed
            error_message = (
                f"All {max_retries} retry attempts failed for {func.__name__}"
            )
            logger.error(error_message)
            raise RetryError(error_message, last_exception)
        
        return cast(Callable[..., T], wrapper)
    
    return decorator


def retry_operation(
    operation: Callable[..., T],
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_backoff: float = 60.0,
    jitter: bool = True,
    exceptions_to_retry: Optional[List[Type[Exception]]] = None,
    logger: Optional[logging.Logger] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Retry an operation with exponential backoff.
    
    This function provides the same functionality as the retry_with_backoff decorator
    but can be used directly with any function.
    
    Args:
        operation: Function to retry
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for backoff time after each retry
        max_backoff: Maximum backoff time in seconds
        jitter: Whether to add random jitter to backoff time
        exceptions_to_retry: List of exception types to retry on (defaults to all exceptions)
        logger: Optional logger instance
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
        
    Returns:
        Result of the operation
        
    Raises:
        RetryError: If all retry attempts fail
    """
    logger = logger or DevSynthLogger(__name__)
    
    retry_count = 0
    backoff = initial_backoff
    last_exception = None
    
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                logger.info(
                    f"Retry attempt {retry_count}/{max_retries} for {operation.__name__}"
                )
            return operation(*args, **kwargs)
        except Exception as e:
            # Check if we should retry this exception
            if (exceptions_to_retry is not None and 
                    not any(isinstance(e, exc) for exc in exceptions_to_retry)):
                logger.warning(
                    f"Exception {type(e).__name__} not in retry list, re-raising"
                )
                raise
            
            last_exception = e
            retry_count += 1
            
            if retry_count > max_retries:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for {operation.__name__}"
                )
                break
            
            # Calculate backoff time with jitter
            actual_backoff = min(backoff, max_backoff)
            if jitter:
                # Add random jitter between 0% and 25%
                jitter_amount = random.uniform(0, 0.25 * actual_backoff)
                actual_backoff += jitter_amount
            
            logger.warning(
                f"Attempt {retry_count} failed with {type(e).__name__}: {e}. "
                f"Retrying in {actual_backoff:.2f} seconds..."
            )
            
            # Wait before retrying
            time.sleep(actual_backoff)
            
            # Increase backoff for next attempt
            backoff *= backoff_multiplier
    
    # If we get here, all retries failed
    error_message = (
        f"All {max_retries} retry attempts failed for {operation.__name__}"
    )
    logger.error(error_message)
    raise RetryError(error_message, last_exception)


class RetryConfig:
    """Configuration for retry operations."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 60.0,
        jitter: bool = True,
        exceptions_to_retry: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            backoff_multiplier: Multiplier for backoff time after each retry
            max_backoff: Maximum backoff time in seconds
            jitter: Whether to add random jitter to backoff time
            exceptions_to_retry: List of exception types to retry on (defaults to all exceptions)
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.jitter = jitter
        self.exceptions_to_retry = exceptions_to_retry


# Default retry configurations for different types of operations
DEFAULT_RETRY_CONFIG = RetryConfig()

# Configuration for quick retries (shorter backoff)
QUICK_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_backoff=0.1,
    backoff_multiplier=1.5,
    max_backoff=5.0
)

# Configuration for persistent retries (more attempts, longer backoff)
PERSISTENT_RETRY_CONFIG = RetryConfig(
    max_retries=10,
    initial_backoff=2.0,
    backoff_multiplier=2.0,
    max_backoff=300.0
)

# Configuration for network operations
NETWORK_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_backoff=1.0,
    backoff_multiplier=2.0,
    max_backoff=60.0,
    exceptions_to_retry=[
        ConnectionError,
        TimeoutError,
        OSError
    ]
)

# Configuration for memory operations
MEMORY_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    initial_backoff=0.1,
    backoff_multiplier=2.0,
    max_backoff=2.0
)


def retry_memory_operation(
    max_retries: int = 3,
    initial_backoff: float = 0.1,
    max_backoff: float = 2.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator specifically for memory operations with appropriate defaults.
    
    This is a convenience wrapper around retry_with_backoff with defaults
    suitable for memory operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        
    Returns:
        Decorator function
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        backoff_multiplier=2.0,
        max_backoff=max_backoff,
        jitter=True
    )


def with_retry(
    retry_config: Optional[RetryConfig] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying a function with the specified retry configuration.
    
    Args:
        retry_config: Retry configuration to use (defaults to DEFAULT_RETRY_CONFIG)
        
    Returns:
        Decorator function
    """
    config = retry_config or DEFAULT_RETRY_CONFIG
    
    return retry_with_backoff(
        max_retries=config.max_retries,
        initial_backoff=config.initial_backoff,
        backoff_multiplier=config.backoff_multiplier,
        max_backoff=config.max_backoff,
        jitter=config.jitter,
        exceptions_to_retry=config.exceptions_to_retry
    )