"""Retry helpers for memory operations and supporting infrastructure.

The utilities in this module coordinate retries around DevSynth memory
operations.  They integrate with circuit breakers, Prometheus counters, and
DTOs provided by :mod:`devsynth.application.memory.dto`.  Type annotations are
kept intentionally strict so static analyzers understand the shapes exchanged
between retry callbacks and the decorated callables.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable, Mapping, Sequence
from functools import wraps
from typing import Protocol, Type, TypeAlias, TypeVar, cast


# ``prometheus_client`` is an optional dependency. Import it lazily and
# degrade to no-op metrics when unavailable so that memory logic remains
# functional in lightweight environments.
class CounterAPI(Protocol):
    """Protocol describing the subset of Prometheus counter behaviour we use."""

    def labels(
        self, *args: object, **kwargs: object
    ) -> CounterAPI:  # pragma: no cover - protocol
        ...

    def inc(self, amount: float = 1.0) -> None:  # pragma: no cover - protocol
        ...

    def clear(self) -> None:  # pragma: no cover - protocol
        ...


class _CounterWrapper:
    """Lightweight adapter that mirrors the Prometheus ``Counter`` API."""

    __slots__ = ("_counter",)

    def __init__(self, counter: object) -> None:
        self._counter = counter

    def labels(self, *args: object, **kwargs: object) -> CounterAPI:
        method = getattr(self._counter, "labels", None)
        if callable(method):
            return _CounterWrapper(method(*args, **kwargs))
        return self

    def inc(self, amount: float = 1.0) -> None:
        method = getattr(self._counter, "inc", None)
        if callable(method):
            method(amount)

    def clear(self) -> None:
        method = getattr(self._counter, "clear", None)
        if callable(method):
            method()


class _NoOpCounter:
    """Fallback counter used when Prometheus is unavailable."""

    __slots__ = ()

    def labels(self, *args: object, **kwargs: object) -> CounterAPI:
        return self

    def inc(self, amount: float = 1.0) -> None:
        return None

    def clear(self) -> None:
        return None


def _create_counter(
    name: str, documentation: str, labelnames: Sequence[str]
) -> CounterAPI:
    """Build a Prometheus counter or a no-op placeholder when unavailable."""

    prometheus_counter_cls: type[object] | None
    try:  # pragma: no cover - import guarded for optional dependency
        from prometheus_client import REGISTRY
        from prometheus_client import Counter as PrometheusCounter

        prometheus_counter_cls = PrometheusCounter
    except Exception:  # pragma: no cover - fallback for minimal environments
        prometheus_counter_cls = None

    if prometheus_counter_cls is None:  # pragma: no cover - runtime fallback
        return _NoOpCounter()

    # Try to create the counter, but if it already exists, return the existing one
    try:
        counter = prometheus_counter_cls(name, documentation, list(labelnames))
    except ValueError as e:
        if "Duplicated timeseries" in str(e):
            # Counter already exists, try to retrieve it from the registry
            try:
                counter = REGISTRY._names_to_collectors[name]
            except KeyError:
                # If we can't retrieve it, fall back to no-op
                return _NoOpCounter()
        else:
            raise

    return _CounterWrapper(counter)


from devsynth.application.memory.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    get_circuit_breaker_registry,
)
from devsynth.application.memory.dto import (
    GroupedMemoryResults,
    MemoryQueryResults,
    MemoryRecord,
)
from devsynth.logging_setup import DevSynthLogger

MemoryRetryResult: TypeAlias = (
    MemoryRecord | list[MemoryRecord] | MemoryQueryResults | GroupedMemoryResults | None
)

"""Result types commonly emitted by retryable memory callables."""


class ConditionCallback(Protocol):
    """Callable signature used to determine whether a retry should proceed."""

    def __call__(
        self, error: Exception, attempt: int
    ) -> bool:  # pragma: no cover - protocol
        ...


class MemoryConditionCallback(Protocol):
    """Condition callback that can inspect DTO-centric retry payloads."""

    def __call__(
        self, error: Exception, attempt: int, payload: MemoryRetryResult
    ) -> bool:  # pragma: no cover - protocol
        ...


class RetryCondition(Protocol):
    """Predicate evaluated against an exception to gate retries."""

    def __call__(self, error: Exception) -> bool:  # pragma: no cover - protocol
        ...


__all__ = [
    "RetryError",
    "retry_with_backoff",
    "retry_operation",
    "RetryConfig",
    "DEFAULT_RETRY_CONFIG",
    "QUICK_RETRY_CONFIG",
    "PERSISTENT_RETRY_CONFIG",
    "NETWORK_RETRY_CONFIG",
    "MEMORY_RETRY_CONFIG",
    "retry_event_counter",
    "retry_function_counter",
    "retry_error_counter",
    "retry_condition_counter",
    "retry_stat_counter",
    "ANONYMOUS_CONDITION",
    "reset_memory_retry_metrics",
]

T = TypeVar("T")


class RetryError(Exception):
    """Exception raised when all retry attempts fail."""

    def __init__(self, message: str, last_exception: Exception | None = None):
        """
        Initialize the retry error.

        Args:
            message: Error message
            last_exception: The last exception that was caught during retry
        """
        super().__init__(message)
        self.last_exception = last_exception


retry_event_counter: CounterAPI = _create_counter(
    "devsynth_memory_retry_events_total",
    "Retry events for memory operations",
    ["status"],
)
retry_function_counter: CounterAPI = _create_counter(
    "devsynth_memory_retry_function_total",
    "Memory retry attempts per function",
    ["function"],
)
retry_error_counter: CounterAPI = _create_counter(
    "devsynth_memory_retry_errors_total",
    "Memory retry events per exception type",
    ["error_type"],
)

retry_condition_counter: CounterAPI = _create_counter(
    "devsynth_memory_retry_conditions_total",
    "Memory retry events grouped by failed condition name",
    ["condition"],
)

retry_stat_counter: CounterAPI = _create_counter(
    "devsynth_memory_retry_stat_total",
    "Memory retry outcomes grouped by function and status",
    ["function", "status"],
)

ANONYMOUS_CONDITION = "<anonymous>"


def reset_memory_retry_metrics() -> None:
    """Reset Prometheus counters for memory retries."""
    retry_event_counter.clear()
    retry_function_counter.clear()
    retry_error_counter.clear()
    retry_condition_counter.clear()
    retry_stat_counter.clear()


def _adapt_memory_condition_callbacks(
    callbacks: Sequence[MemoryConditionCallback] | None,
) -> list[ConditionCallback] | None:
    """Bridge memory-aware callbacks to the generic retry signature."""

    if not callbacks:
        return None

    adapted: list[ConditionCallback] = []
    for cb_fn in callbacks:

        def adapter(
            error: Exception,
            attempt: int,
            *,
            _cb: MemoryConditionCallback = cb_fn,
        ) -> bool:
            payload: MemoryRetryResult = None
            return _cb(error, attempt, payload)

        adapted.append(adapter)
    return adapted


def retry_with_backoff(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_backoff: float = 60.0,
    jitter: bool = True,
    exceptions_to_retry: Sequence[type[Exception]] | None = None,
    logger: logging.Logger | None = None,
    condition_callbacks: Sequence[ConditionCallback] | None = None,
    retry_conditions: (
        Sequence[RetryCondition | str] | Mapping[str, RetryCondition | str] | None
    ) = None,
    track_metrics: bool = True,
    circuit_breaker_name: str | None = None,
    circuit_breaker_failure_threshold: int = 3,
    circuit_breaker_reset_timeout: float = 60.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for backoff time after each retry
        max_backoff: Maximum backoff time in seconds
        jitter: Whether to add random jitter to backoff time
        exceptions_to_retry: Sequence of exception types to retry on (defaults to all exceptions)
        logger: Optional logger instance
        condition_callbacks: Optional sequence of callbacks invoked after each
            exception to determine if retry should continue
        retry_conditions: Optional sequence or mapping of additional conditions that
            must evaluate to ``True`` for retries to continue. String entries
            are treated as substrings that must appear in the exception message.
        track_metrics: Whether to track Prometheus metrics
        circuit_breaker_name: Name of circuit breaker to use for protecting the
            wrapped function. If provided, retries abort when the circuit
            breaker opens.
        circuit_breaker_failure_threshold: Failures allowed before opening the
            circuit breaker
        circuit_breaker_reset_timeout: Time in seconds before the circuit
            breaker transitions from OPEN to HALF-OPEN

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            nonlocal logger
            logger = logger or DevSynthLogger(__name__)
            func_name = getattr(func, "__name__", "<unknown>")

            retry_count = 0
            backoff = initial_backoff
            last_exception: Exception | None = None
            callbacks = list(condition_callbacks) if condition_callbacks else []
            anonymous_conditions: list[RetryCondition] = []
            named_conditions: list[tuple[str, RetryCondition]] = []
            if retry_conditions:
                if isinstance(retry_conditions, Mapping):
                    for name, cond in retry_conditions.items():
                        if isinstance(cond, str):
                            named_conditions.append(
                                (name, lambda exc, substr=cond: substr in str(exc))
                            )
                        elif callable(cond):
                            named_conditions.append((name, cond))
                        else:  # pragma: no cover - defensive
                            raise TypeError(
                                "retry_conditions values must be callables or strings"
                            )
                elif isinstance(retry_conditions, str):
                    raise TypeError(
                        "retry_conditions must not be provided as a plain string"
                    )
                else:
                    for cond in retry_conditions:
                        if isinstance(cond, str):
                            anonymous_conditions.append(
                                lambda exc, substr=cond: substr in str(exc)
                            )
                        elif callable(cond):
                            anonymous_conditions.append(cond)
                        else:  # pragma: no cover - defensive
                            raise TypeError(
                                "retry_conditions must be callables or strings"
                            )
            cb: CircuitBreaker | None = None
            if circuit_breaker_name:
                registry = get_circuit_breaker_registry()
                cb = registry.get_or_create(
                    name=circuit_breaker_name,
                    failure_threshold=circuit_breaker_failure_threshold,
                    reset_timeout=circuit_breaker_reset_timeout,
                )

            while retry_count <= max_retries:
                try:
                    if retry_count > 0:
                        logger.info(
                            f"Retry attempt {retry_count}/{max_retries} for {func_name}"
                        )
                    if cb:
                        result = cb.execute(func, *args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    if track_metrics:
                        retry_event_counter.labels(status="success").inc()
                        retry_stat_counter.labels(
                            function=func_name, status="success"
                        ).inc()
                    return result
                except CircuitBreakerOpenError as e:
                    logger.warning(
                        f"Circuit breaker '{circuit_breaker_name}' is open, aborting retries"
                    )
                    if track_metrics:
                        retry_event_counter.labels(status="abort").inc()
                        retry_error_counter.labels(error_type=type(e).__name__).inc()
                        retry_stat_counter.labels(
                            function=func_name, status="abort"
                        ).inc()
                    raise
                except Exception as e:
                    if exceptions_to_retry is not None and not any(
                        isinstance(e, exc) for exc in exceptions_to_retry
                    ):
                        logger.warning(
                            f"Exception {type(e).__name__} not in retry list, re-raising",
                        )
                        if track_metrics:
                            retry_event_counter.labels(status="abort").inc()
                            retry_error_counter.labels(
                                error_type=type(e).__name__
                            ).inc()
                            retry_stat_counter.labels(
                                function=func_name, status="abort"
                            ).inc()
                        raise

                    for name, cond in named_conditions:
                        cond_result = cond(e)
                        if track_metrics:
                            outcome = "trigger" if cond_result else "suppress"
                            retry_condition_counter.labels(
                                condition=f"{name}:{outcome}"
                            ).inc()
                        if not cond_result:
                            logger.warning(
                                "Not retrying %s due to retry_conditions policy (%s): %s",
                                func_name,
                                name,
                                e,
                            )
                            if track_metrics:
                                retry_event_counter.labels(status="abort").inc()
                                retry_error_counter.labels(
                                    error_type=type(e).__name__
                                ).inc()
                                retry_stat_counter.labels(
                                    function=func_name, status="abort"
                                ).inc()
                            raise

                    if anonymous_conditions:
                        anon_results = [cond(e) for cond in anonymous_conditions]
                        if track_metrics:
                            for res in anon_results:
                                outcome = "trigger" if res else "suppress"
                                retry_condition_counter.labels(
                                    condition=f"{ANONYMOUS_CONDITION}:{outcome}"
                                ).inc()
                        if not all(anon_results):
                            logger.warning(
                                "Not retrying %s due to retry_conditions policy: %s",
                                func_name,
                                e,
                            )
                            if track_metrics:
                                retry_event_counter.labels(status="abort").inc()
                                retry_error_counter.labels(
                                    error_type=type(e).__name__
                                ).inc()
                                retry_stat_counter.labels(
                                    function=func_name, status="abort"
                                ).inc()
                            raise

                    if callbacks:
                        cb_results: list[bool] = []
                        for cb_fn in callbacks:
                            try:
                                res = cb_fn(e, retry_count)
                            except Exception as cb_error:
                                callback_name = getattr(
                                    cb_fn, "__name__", ANONYMOUS_CONDITION
                                )
                                logger.warning(
                                    "Error in condition callback %s while retrying %s: %s",
                                    callback_name,
                                    func_name,
                                    cb_error,
                                )
                                res = False
                            if track_metrics:
                                outcome = "trigger" if res else "suppress"
                                retry_condition_counter.labels(
                                    condition=f"{getattr(cb_fn, '__name__', ANONYMOUS_CONDITION)}:{outcome}"
                                ).inc()
                            cb_results.append(res)
                        if not all(cb_results):
                            if track_metrics:
                                retry_event_counter.labels(status="abort").inc()
                                retry_error_counter.labels(
                                    error_type=type(e).__name__
                                ).inc()
                                retry_stat_counter.labels(
                                    function=func_name, status="abort"
                                ).inc()
                            raise
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func_name}"
                        )
                        if track_metrics:
                            retry_event_counter.labels(status="failure").inc()
                            retry_error_counter.labels(
                                error_type=type(e).__name__
                            ).inc()
                            retry_stat_counter.labels(
                                function=func_name, status="failure"
                            ).inc()
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
                    if track_metrics:
                        retry_event_counter.labels(status="attempt").inc()
                        retry_function_counter.labels(function=func_name).inc()
                        retry_error_counter.labels(error_type=type(e).__name__).inc()
                        retry_stat_counter.labels(
                            function=func_name, status="attempt"
                        ).inc()

                    # Wait before retrying
                    time.sleep(actual_backoff)

                    # Increase backoff for next attempt
                    backoff *= backoff_multiplier

            # If we get here, all retries failed
            error_message = f"All {max_retries} retry attempts failed for {func_name}"
            logger.error(error_message)
            if track_metrics and last_exception is not None:
                retry_event_counter.labels(status="failure").inc()
                retry_error_counter.labels(
                    error_type=type(last_exception).__name__
                ).inc()
                retry_stat_counter.labels(function=func_name, status="failure").inc()
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
    exceptions_to_retry: Sequence[type[Exception]] | None = None,
    logger: logging.Logger | None = None,
    condition_callbacks: Sequence[ConditionCallback] | None = None,
    retry_conditions: (
        Sequence[RetryCondition | str] | Mapping[str, RetryCondition | str] | None
    ) = None,
    track_metrics: bool = True,
    circuit_breaker_name: str | None = None,
    circuit_breaker_failure_threshold: int = 3,
    circuit_breaker_reset_timeout: float = 60.0,
    *args: object,
    **kwargs: object,
) -> T:
    """Retry an operation with exponential backoff."""

    decorated = retry_with_backoff(
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        backoff_multiplier=backoff_multiplier,
        max_backoff=max_backoff,
        jitter=jitter,
        exceptions_to_retry=exceptions_to_retry,
        logger=logger,
        condition_callbacks=condition_callbacks,
        retry_conditions=retry_conditions,
        track_metrics=track_metrics,
        circuit_breaker_name=circuit_breaker_name,
        circuit_breaker_failure_threshold=circuit_breaker_failure_threshold,
        circuit_breaker_reset_timeout=circuit_breaker_reset_timeout,
    )(operation)
    return decorated(*args, **kwargs)


class RetryConfig:
    """Configuration for retry operations."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 60.0,
        jitter: bool = True,
        exceptions_to_retry: Sequence[type[Exception]] | None = None,
        condition_callbacks: Sequence[ConditionCallback] | None = None,
        retry_conditions: (
            Sequence[RetryCondition | str] | Mapping[str, RetryCondition | str] | None
        ) = None,
        circuit_breaker_name: str | None = None,
        circuit_breaker_failure_threshold: int = 3,
        circuit_breaker_reset_timeout: float = 60.0,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            backoff_multiplier: Multiplier for backoff time after each retry
            max_backoff: Maximum backoff time in seconds
            jitter: Whether to add random jitter to backoff time
            exceptions_to_retry: Sequence of exception types to retry on (defaults to all exceptions)
            condition_callbacks: Optional sequence of callbacks to determine if retry should continue
            retry_conditions: Optional sequence or mapping of additional conditions that must evaluate
                to ``True`` for retries to continue
            circuit_breaker_name: Optional name of circuit breaker to use
            circuit_breaker_failure_threshold: Failures allowed before opening circuit breaker
            circuit_breaker_reset_timeout: Seconds before circuit breaker tries to close
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.jitter = jitter
        self.exceptions_to_retry = exceptions_to_retry
        self.condition_callbacks = condition_callbacks
        self.retry_conditions = retry_conditions
        self.circuit_breaker_name = circuit_breaker_name
        self.circuit_breaker_failure_threshold = circuit_breaker_failure_threshold
        self.circuit_breaker_reset_timeout = circuit_breaker_reset_timeout


# Default retry configurations for different types of operations
DEFAULT_RETRY_CONFIG = RetryConfig()

# Configuration for quick retries (shorter backoff)
QUICK_RETRY_CONFIG = RetryConfig(
    max_retries=5, initial_backoff=0.1, backoff_multiplier=1.5, max_backoff=5.0
)

# Configuration for persistent retries (more attempts, longer backoff)
PERSISTENT_RETRY_CONFIG = RetryConfig(
    max_retries=10, initial_backoff=2.0, backoff_multiplier=2.0, max_backoff=300.0
)

# Configuration for network operations
NETWORK_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_backoff=1.0,
    backoff_multiplier=2.0,
    max_backoff=60.0,
    exceptions_to_retry=[ConnectionError, TimeoutError, OSError],
)

# Configuration for memory operations
MEMORY_RETRY_CONFIG = RetryConfig(
    max_retries=3, initial_backoff=0.1, backoff_multiplier=2.0, max_backoff=2.0
)


def retry_memory_operation(
    max_retries: int = 3,
    initial_backoff: float = 0.1,
    max_backoff: float = 2.0,
    *,
    condition_callbacks: Sequence[MemoryConditionCallback] | None = None,
) -> Callable[[Callable[..., MemoryRetryResult]], Callable[..., MemoryRetryResult]]:
    """
    Decorator specifically for memory operations with DTO-aware typing.

    This is a convenience wrapper around :func:`retry_with_backoff` with
    defaults suitable for memory operations.  The returned decorator preserves
    the :class:`MemoryRecord`-centric result types exposed by memory adapters
    and allows condition callbacks that receive an optional ``MemoryRecord``
    context.

    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        condition_callbacks: Optional callbacks invoked after each failure.
            Each callback receives the triggering exception, the current retry
            attempt, and the :class:`MemoryRecord` (if available) responsible
            for the failure.  When no record context exists ``None`` is
            supplied.

    Returns:
        Decorator function
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        backoff_multiplier=2.0,
        max_backoff=max_backoff,
        jitter=True,
        condition_callbacks=_adapt_memory_condition_callbacks(condition_callbacks),
    )


def with_retry(
    retry_config: RetryConfig | None = None,
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
        exceptions_to_retry=config.exceptions_to_retry,
        condition_callbacks=config.condition_callbacks,
        retry_conditions=config.retry_conditions,
        circuit_breaker_name=config.circuit_breaker_name,
        circuit_breaker_failure_threshold=config.circuit_breaker_failure_threshold,
        circuit_breaker_reset_timeout=config.circuit_breaker_reset_timeout,
    )
