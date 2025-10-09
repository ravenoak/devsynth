"""Fallback mechanisms for graceful degradation in the DevSynth system."""

from __future__ import annotations

import functools
import random
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from typing import ParamSpec, TypedDict, TypeVar

from .exceptions import DevSynthError
from .logging_setup import DevSynthLogger
from .metrics import (
    circuit_breaker_state_counter,
    get_circuit_breaker_state_metrics,
    get_retry_condition_metrics,
    get_retry_count_metrics,
    get_retry_error_metrics,
    get_retry_metrics,
    get_retry_stat_metrics,
    inc_circuit_breaker_state,
    inc_retry,
    inc_retry_condition,
    inc_retry_count,
    inc_retry_error,
    inc_retry_stat,
    reset_metrics,
    retry_condition_counter,
    retry_error_counter,
    retry_event_counter,
    retry_function_counter,
    retry_stat_counter,
)

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")
ResultT = TypeVar("ResultT")
P = ParamSpec("P")
Q = ParamSpec("Q")


RetryConditionFunc = Callable[[Exception], bool]
RetryConditionSpec = RetryConditionFunc | str | type[BaseException]
RetryConditions = Sequence[RetryConditionSpec] | Mapping[str, RetryConditionSpec]

ConditionCallbackFunc = Callable[[Exception, int], bool]
ConditionCallbacks = (
    Sequence[ConditionCallbackFunc] | Mapping[str, ConditionCallbackFunc]
)

FallbackConditionFunc = Callable[[Exception], bool]
FallbackConditionSpec = FallbackConditionFunc | str
FallbackConditions = (
    Sequence[FallbackConditionSpec] | Mapping[str, FallbackConditionSpec]
)


class RetryPolicy(TypedDict, total=False):
    retry: bool
    max_retries: int


ErrorRetryMap = Mapping[type[BaseException], bool | RetryPolicy]

# Create a logger for this module
logger = DevSynthLogger("fallback")

# Placeholder name used for metrics when anonymous retry conditions fail
ANONYMOUS_CONDITION = "<anonymous>"


def _substring_condition(substring: str) -> RetryConditionFunc:
    def _matches_message(exc: Exception) -> bool:
        return substring in str(exc)

    return _matches_message


def _exception_condition(exception_type: type[BaseException]) -> RetryConditionFunc:
    def _matches_type(exc: Exception) -> bool:
        return isinstance(exc, exception_type)

    return _matches_type


def _condition_from_spec(spec: RetryConditionSpec) -> RetryConditionFunc:
    if isinstance(spec, str):
        return _substring_condition(spec)
    if isinstance(spec, type) and issubclass(spec, BaseException):
        return _exception_condition(spec)
    return spec


def _status_code_predicate(code: int) -> Callable[[ResultT], bool]:
    def _matches_status(result: ResultT) -> bool:
        return getattr(result, "status_code", None) == code

    return _matches_status


def _predicate_from_spec(
    value: Callable[[ResultT], bool] | int,
) -> Callable[[ResultT], bool]:
    if isinstance(value, int):
        return _status_code_predicate(value)
    return value


def _fallback_condition_from_spec(
    spec: FallbackConditionSpec,
) -> FallbackConditionFunc:
    if isinstance(spec, str):
        return _substring_condition(spec)
    return spec


def reset_prometheus_metrics() -> None:
    """Reset all retry metrics and Prometheus counters."""
    reset_metrics()


# Export metrics helpers for convenience
__all__ = [
    "retry_with_exponential_backoff",
    "with_fallback",
    "FallbackHandler",
    "CircuitBreaker",
    "Bulkhead",
    "get_retry_metrics",
    "get_retry_count_metrics",
    "get_retry_condition_metrics",
    "get_retry_error_metrics",
    "get_retry_stat_metrics",
    "retry_event_counter",
    "retry_function_counter",
    "retry_error_counter",
    "retry_condition_counter",
    "retry_stat_counter",
    "circuit_breaker_state_counter",
    "get_circuit_breaker_state_metrics",
    "ANONYMOUS_CONDITION",
    "reset_prometheus_metrics",
]


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[Exception, int, float], None] | None = None,
    should_retry: Callable[[Exception], bool] | None = None,
    retry_conditions: RetryConditions | None = None,
    condition_callbacks: ConditionCallbacks | None = None,
    retry_predicates: (
        Sequence[Callable[[T], bool] | int]
        | Mapping[str, Callable[[T], bool] | int]
        | None
    ) = None,
    retry_on_result: Callable[[T], bool] | None = None,
    track_metrics: bool = True,
    error_retry_map: ErrorRetryMap | None = None,
    circuit_breaker: "CircuitBreaker" | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
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
    retry_conditions : Optional[Union[List[Union[Callable[[Exception], bool], str, type]],
                                     Dict[str, Union[Callable[[Exception], bool], str, type]]]]
        Additional per-exception conditions that must all evaluate to ``True``
        for the retry to continue. ``retry_conditions`` may be either a list or
        a dictionary. When a dictionary is provided the keys name each
        condition and metrics are recorded for any condition that fails.
        String entries are treated as substrings that must appear in the
        exception message. Exception classes are matched using
        ``isinstance`` against the raised exception.
    condition_callbacks : Optional[
        Union[
            List[Callable[[Exception, int], bool]],
            Dict[str, Callable[[Exception, int], bool]],
        ]
    ]
        Callbacks invoked with the exception and current retry attempt. When a
        dictionary is supplied the keys name each callback for metric
        reporting. All callbacks must return ``True`` for the retry loop to
        continue.
    retry_predicates : Optional[Union[List[Union[Callable[[T], bool], int]],
                                      Dict[str, Union[Callable[[T], bool], int]]]]
        Predicates evaluated on successful results. If any predicate returns
        ``True`` the result is treated as a failure and retried. Integer entries
        are interpreted as HTTP status codes and compared to a ``status_code``
        attribute on the result if present.
    retry_on_result : Optional[Callable[[T], bool]]
        Predicate executed on successful results. If it returns ``True`` a
        retry is triggered as if an exception had been raised.
    track_metrics : bool
        When ``True`` retry attempts are recorded via
        :mod:`devsynth.metrics` and Prometheus counters.
    error_retry_map : Optional[Dict[type, Union[bool, Dict[str, Union[int, bool]]]]]
        Mapping of exception types to retry policies. Values may be either a
        boolean or a dictionary. ``False`` aborts the retry loop when that error
        is encountered while ``True`` forces a retry even if the exception is not
        listed in ``retryable_exceptions``. When a dictionary is provided the
        following keys are recognized. Policies match subclasses of the mapped
        exception type and metrics record whether a policy permits or suppresses
        retries:

        ``retry``: ``bool``
            Whether retries are permitted (defaults to ``True``).
        ``max_retries``: ``int``
            Maximum retries for this error type overriding ``max_retries``.
    circuit_breaker : Optional["CircuitBreaker"]
        Circuit breaker instance used to guard function calls. If provided,
        each retry attempt is executed through the circuit breaker.

    Returns
    -------
    Callable
        A decorator function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        wrapped_func = circuit_breaker(func) if circuit_breaker else func

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Initialize variables
            num_retries = 0
            delay = initial_delay
            anonymous_conditions: list[RetryConditionFunc] = []
            named_conditions: list[tuple[str, RetryConditionFunc]] = []
            if retry_conditions is not None:
                if isinstance(retry_conditions, Mapping):
                    for name, cond in retry_conditions.items():
                        named_conditions.append((name, _condition_from_spec(cond)))
                else:
                    if isinstance(retry_conditions, (str, bytes)):
                        raise TypeError(
                            "retry_conditions must be a sequence of callables, strings, or exception types"
                        )
                    for cond in retry_conditions:
                        anonymous_conditions.append(_condition_from_spec(cond))
            cb_named: list[tuple[str, ConditionCallbackFunc]] = []
            cb_anon: list[ConditionCallbackFunc] = []
            if condition_callbacks is not None:
                if isinstance(condition_callbacks, Mapping):
                    for name, cb in condition_callbacks.items():
                        cb_named.append((name, cb))
                else:
                    if isinstance(condition_callbacks, (str, bytes)):
                        raise TypeError(
                            "condition_callbacks must be a sequence of callables"
                        )
                    cb_anon = list(condition_callbacks)

            anonymous_predicates: list[Callable[[T], bool]] = []
            named_predicates: list[tuple[str, Callable[[T], bool]]] = []
            if retry_predicates is not None:
                if isinstance(retry_predicates, Mapping):
                    for name, pred in retry_predicates.items():
                        named_predicates.append((name, _predicate_from_spec(pred)))
                else:
                    if isinstance(retry_predicates, (str, bytes)):
                        raise TypeError(
                            "retry_predicates must be a sequence of callables or ints"
                        )
                    anonymous_predicates = [
                        _predicate_from_spec(pred) for pred in retry_predicates
                    ]

            # Loop until max retries reached
            while True:
                try:
                    result = wrapped_func(*args, **kwargs)
                    if retry_on_result and retry_on_result(result):
                        raise ValueError("retry_on_result triggered")
                    if named_predicates or anonymous_predicates:
                        pred_results: list[bool] = []
                        for name, pred in named_predicates:
                            res = pred(result)
                            pred_results.append(res)
                            if track_metrics:
                                outcome = "trigger" if res else "suppress"
                                inc_retry_condition(f"predicate:{name}:{outcome}")
                        if anonymous_predicates:
                            anon_results = [
                                pred(result) for pred in anonymous_predicates
                            ]
                            if track_metrics:
                                for res in anon_results:
                                    outcome = "trigger" if res else "suppress"
                                    inc_retry_condition(
                                        f"predicate:{ANONYMOUS_CONDITION}:{outcome}"
                                    )
                            pred_results.extend(anon_results)
                        if any(pred_results):
                            raise ValueError("retry_predicate triggered")
                    if track_metrics:
                        inc_retry("success")
                        inc_retry_stat(func.__name__, "success")
                    return result
                except Exception as e:
                    policy_max_retries = max_retries
                    policy_retry: bool | None = None
                    policy_name: str | None = None
                    if error_retry_map is not None:
                        for exc_type, policy in error_retry_map.items():
                            if isinstance(e, exc_type):
                                policy_name = exc_type.__name__
                                if isinstance(policy, bool):
                                    policy_retry = policy
                                else:
                                    policy_retry = policy.get("retry", True)
                                    policy_max_retries = policy.get(
                                        "max_retries", max_retries
                                    )
                                break

                    retry_allowed = (
                        isinstance(e, retryable_exceptions)
                        if policy_retry is None
                        else policy_retry
                    )
                    if track_metrics and policy_name is not None:
                        outcome = "trigger" if retry_allowed else "suppress"
                        inc_retry_condition(f"policy:{policy_name}:{outcome}")

                    if (
                        isinstance(e, ValueError)
                        and str(e) == "retry_on_result triggered"
                    ):
                        num_retries += 1
                        if num_retries > policy_max_retries:
                            if track_metrics:
                                inc_retry("failure")
                                inc_retry_error("InvalidResult")
                                inc_retry_stat(func.__name__, "failure")
                            raise
                        if track_metrics:
                            inc_retry("invalid")
                            inc_retry_error("InvalidResult")
                            inc_retry_stat(func.__name__, "attempt")
                        if jitter:
                            delay = min(
                                max_delay,
                                delay * exponential_base * (0.5 + random.random()),
                            )
                        else:
                            delay = min(max_delay, delay * exponential_base)
                        logger.warning(
                            f"Retrying due to invalid result {num_retries}/{policy_max_retries} after {delay:.2f}s",
                            function=func.__name__,
                            retry_attempt=num_retries,
                            delay=delay,
                        )
                        time.sleep(delay)
                        continue

                    if (
                        isinstance(e, ValueError)
                        and str(e) == "retry_predicate triggered"
                    ):
                        num_retries += 1
                        if num_retries > policy_max_retries:
                            if track_metrics:
                                inc_retry("failure")
                                inc_retry_error("RetryPredicate")
                                inc_retry_stat(func.__name__, "failure")
                            raise
                        if track_metrics:
                            inc_retry("predicate")
                            inc_retry_error("RetryPredicate")
                            inc_retry_stat(func.__name__, "attempt")
                        if jitter:
                            delay = min(
                                max_delay,
                                delay * exponential_base * (0.5 + random.random()),
                            )
                        else:
                            delay = min(max_delay, delay * exponential_base)
                        logger.warning(
                            f"Retrying due to predicate failure {num_retries}/{policy_max_retries} after {delay:.2f}s",
                            function=func.__name__,
                            retry_attempt=num_retries,
                            delay=delay,
                        )
                        time.sleep(delay)
                        continue

                    if not retry_allowed:
                        if track_metrics:
                            inc_retry("abort")
                            inc_retry_error(e.__class__.__name__)
                            inc_retry_stat(func.__name__, "abort")
                        raise
                    if (
                        isinstance(e, DevSynthError)
                        and getattr(e, "error_code", None) == "CIRCUIT_OPEN"
                    ):
                        logger.warning(
                            f"Circuit open - aborting retries for {func.__name__}",
                            error=e,
                            function=func.__name__,
                        )
                        if track_metrics:
                            inc_retry("abort")
                            inc_retry_error(e.__class__.__name__)
                            inc_retry_stat(func.__name__, "abort")
                        raise
                    if should_retry and not should_retry(e):
                        logger.warning(
                            f"Not retrying {func.__name__} due to should_retry policy",
                            error=e,
                            function=func.__name__,
                        )
                        if track_metrics:
                            inc_retry("abort")
                            inc_retry_error(e.__class__.__name__)
                            inc_retry_stat(func.__name__, "abort")
                        raise
                    for name, cond in named_conditions:
                        cond_result = cond(e)
                        if track_metrics:
                            outcome = "trigger" if cond_result else "suppress"
                            inc_retry_condition(f"{name}:{outcome}")
                        if not cond_result:
                            logger.warning(
                                f"Not retrying {func.__name__} due to retry_conditions policy",
                                error=e,
                                function=func.__name__,
                                condition=name,
                            )
                            if track_metrics:
                                inc_retry("abort")
                                inc_retry_error(e.__class__.__name__)
                                inc_retry_stat(func.__name__, "abort")
                            raise
                    if anonymous_conditions:
                        anon_results = [cond(e) for cond in anonymous_conditions]
                        if track_metrics:
                            for res in anon_results:
                                outcome = "trigger" if res else "suppress"
                                inc_retry_condition(f"{ANONYMOUS_CONDITION}:{outcome}")
                        if not all(anon_results):
                            logger.warning(
                                f"Not retrying {func.__name__} due to retry_conditions policy",
                                error=e,
                                function=func.__name__,
                            )
                            if track_metrics:
                                inc_retry("abort")
                                inc_retry_error(e.__class__.__name__)
                                inc_retry_stat(func.__name__, "abort")
                            raise

                    if cb_named or cb_anon:
                        cb_results: list[bool] = []
                        for name, cb in cb_named:
                            try:
                                result = cb(e, num_retries)
                            except Exception as cb_error:
                                logger.warning(
                                    f"Error in condition callback {name}: {cb_error}",
                                    error=cb_error,
                                    function=func.__name__,
                                )
                                result = False
                            if track_metrics:
                                outcome = "trigger" if result else "suppress"
                                inc_retry_condition(f"{name}:{outcome}")
                            cb_results.append(result)
                        for cb in cb_anon:
                            cb_name = getattr(cb, "__name__", ANONYMOUS_CONDITION)
                            try:
                                result = cb(e, num_retries)
                            except Exception as cb_error:
                                logger.warning(
                                    f"Error in condition callback {cb_name}: {cb_error}",
                                    error=cb_error,
                                    function=func.__name__,
                                )
                                result = False
                            if track_metrics:
                                outcome = "trigger" if result else "suppress"
                                inc_retry_condition(f"{cb_name}:{outcome}")
                            cb_results.append(result)

                        if not all(cb_results):
                            logger.warning(
                                f"Not retrying {func.__name__} due to condition callback policy",
                                error=e,
                                function=func.__name__,
                            )
                            if track_metrics:
                                inc_retry("abort")
                                inc_retry_error(e.__class__.__name__)
                                inc_retry_stat(func.__name__, "abort")
                            raise

                    num_retries += 1
                    if num_retries > policy_max_retries:
                        logger.error(
                            f"Maximum retry attempts ({policy_max_retries}) exceeded",
                            error=e,
                            function=func.__name__,
                            max_retries=policy_max_retries,
                        )
                        if track_metrics:
                            inc_retry("failure")
                            inc_retry_error(e.__class__.__name__)
                            inc_retry_stat(func.__name__, "failure")
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
                        f"Retry attempt {num_retries}/{policy_max_retries} after {delay:.2f}s delay",
                        error=e,
                        function=func.__name__,
                        retry_attempt=num_retries,
                        max_retries=policy_max_retries,
                        delay=delay,
                    )
                    if track_metrics:
                        inc_retry("attempt")
                        inc_retry_count(func.__name__)
                        inc_retry_error(e.__class__.__name__)
                        inc_retry_stat(func.__name__, "attempt")

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
    fallback_function: Callable[P, R],
    exceptions_to_catch: tuple[type[BaseException], ...] = (Exception,),
    should_fallback: Callable[[Exception], bool] | None = None,
    log_original_error: bool = True,
    fallback_conditions: FallbackConditions | None = None,
    circuit_breaker: "CircuitBreaker" | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
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
    fallback_conditions : Optional[Union[List[Union[Callable[[Exception], bool], str]], Dict[str, Union[Callable[[Exception], bool], str]]]]
        Additional conditions that must evaluate to ``True`` for the fallback to
        execute. String entries are treated as substrings that must appear in the
        exception message.
    circuit_breaker : Optional["CircuitBreaker"]
        Circuit breaker instance used to guard the primary function.

    Returns
    -------
    Callable
        A decorator function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        wrapped_func = circuit_breaker(func) if circuit_breaker else func

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return wrapped_func(*args, **kwargs)
            except exceptions_to_catch as e:
                if should_fallback and not should_fallback(e):
                    raise

                anonymous_conditions: list[FallbackConditionFunc] = []
                named_conditions: list[tuple[str, FallbackConditionFunc]] = []
                if fallback_conditions is not None:
                    if isinstance(fallback_conditions, Mapping):
                        for name, cond in fallback_conditions.items():
                            named_conditions.append(
                                (name, _fallback_condition_from_spec(cond))
                            )
                    else:
                        if isinstance(fallback_conditions, (str, bytes)):
                            raise TypeError(
                                "fallback_conditions must be a sequence of callables or strings"
                            )
                        anonymous_conditions = [
                            _fallback_condition_from_spec(cond)
                            for cond in fallback_conditions
                        ]

                for name, cond in named_conditions:
                    if not cond(e):
                        if log_original_error:
                            logger.warning(
                                f"Skipping fallback for {func.__name__} due to condition {name}",
                                error=e,
                                function=func.__name__,
                                condition=name,
                            )
                        raise

                if anonymous_conditions and not all(
                    cond(e) for cond in anonymous_conditions
                ):
                    if log_original_error:
                        logger.warning(
                            f"Skipping fallback for {func.__name__} due to fallback_conditions policy",
                            error=e,
                            function=func.__name__,
                        )
                    raise

                if log_original_error:
                    logger.warning(
                        f"Using fallback for {func.__name__} due to error: {str(e)}",
                        error=e,
                        function=func.__name__,
                        fallback_function=fallback_function.__name__,
                    )

                return fallback_function(*args, **kwargs)

        return wrapper

    return decorator


def FallbackHandler(
    fallback_function: Callable[P, R],
    retry_predicates: (
        Sequence[Callable[[R], bool] | int]
        | Mapping[str, Callable[[R], bool] | int]
        | None
    ) = None,
    track_metrics: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that falls back based on predicates and tracks metrics.

    Parameters
    ----------
    fallback_function : Callable
        Function invoked when predicates trigger or the primary raises.
    retry_predicates : Optional[Union[List[Union[Callable[[R], bool], int]],
                                      Dict[str, Union[Callable[[R], bool], int]]]]
        Predicates evaluated on successful results. Integer entries are
        interpreted as HTTP status codes and compared to a ``status_code``
        attribute on the result if present.
    track_metrics : bool
        When ``True`` retry events are recorded using Prometheus counters.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        named_predicates: list[tuple[str, Callable[[R], bool]]] = []
        anonymous_predicates: list[Callable[[R], bool]] = []
        if retry_predicates is not None:
            if isinstance(retry_predicates, Mapping):
                for name, pred in retry_predicates.items():
                    named_predicates.append((name, _predicate_from_spec(pred)))
            else:
                if isinstance(retry_predicates, (str, bytes)):
                    raise TypeError(
                        "retry_predicates must be a sequence of callables or ints"
                    )
                anonymous_predicates = [
                    _predicate_from_spec(pred) for pred in retry_predicates
                ]

        def _record_predicates(
            res: R,
            named: list[tuple[str, Callable[[R], bool]]],
            anon: list[Callable[[R], bool]],
            metrics: bool,
        ) -> bool:
            pred_results: list[bool] = []
            for name, pred in named:
                r = pred(res)
                pred_results.append(r)
                if metrics:
                    outcome = "trigger" if r else "suppress"
                    inc_retry_condition(f"predicate:{name}:{outcome}")
            if anon:
                anon_results = [p(res) for p in anon]
                if metrics:
                    for r in anon_results:
                        outcome = "trigger" if r else "suppress"
                        inc_retry_condition(
                            f"predicate:{ANONYMOUS_CONDITION}:{outcome}"
                        )
                pred_results.extend(anon_results)
            return any(pred_results)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                if track_metrics:
                    inc_retry("attempt")
                    inc_retry_count(func.__name__)
                    inc_retry_error(e.__class__.__name__)
                    inc_retry_stat(func.__name__, "attempt")
                result = fallback_function(*args, **kwargs)
                if track_metrics:
                    inc_retry("success")
                    inc_retry_stat(func.__name__, "success")
                if named_predicates or anonymous_predicates:
                    _record_predicates(
                        result, named_predicates, anonymous_predicates, track_metrics
                    )
                return result

            if named_predicates or anonymous_predicates:
                triggered = _record_predicates(
                    result, named_predicates, anonymous_predicates, track_metrics
                )
                if triggered:
                    if track_metrics:
                        inc_retry("predicate")
                        inc_retry_error("RetryPredicate")
                        inc_retry_count(func.__name__)
                        inc_retry_stat(func.__name__, "attempt")
                    result = fallback_function(*args, **kwargs)
                    if track_metrics:
                        inc_retry("success")
                        inc_retry_stat(func.__name__, "success")
                    _record_predicates(
                        result, named_predicates, anonymous_predicates, track_metrics
                    )
                    return result

            if track_metrics:
                inc_retry("success")
                inc_retry_stat(func.__name__, "success")
            return result

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
        exception_types: tuple[type[BaseException], ...] = (Exception,),
        on_open: Callable[[str], None] | None = None,
        on_close: Callable[[str], None] | None = None,
        on_half_open: Callable[[str], None] | None = None,
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
        on_open : Optional[Callable[[str], None]]
            Hook executed when the breaker transitions to OPEN.
        on_close : Optional[Callable[[str], None]]
            Hook executed when the breaker transitions to CLOSED.
        on_half_open : Optional[Callable[[str], None]]
            Hook executed when the breaker transitions to HALF_OPEN.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.test_calls = test_calls
        self.exception_types = exception_types
        self.on_open = on_open
        self.on_close = on_close
        self.on_half_open = on_half_open

        # State variables
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.test_calls_remaining = 0

        # Lock for thread-safe state transitions
        self.lock = threading.Lock()

        # Create a logger
        self.logger = DevSynthLogger("circuit_breaker")

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
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
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
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
                inc_circuit_breaker_state(func.__name__, self.HALF_OPEN)
                self.logger.info(
                    f"Circuit breaker for {func.__name__} transitioned from OPEN to HALF_OPEN",
                    function=func.__name__,
                    state=self.state,
                )
                self._safe_hook(self.on_half_open, func.__name__)
            else:
                inc_circuit_breaker_state(func.__name__, self.OPEN)
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
                        inc_circuit_breaker_state(func.__name__, self.CLOSED)
                        self.logger.info(
                            f"Circuit breaker for {func.__name__} transitioned from HALF_OPEN to CLOSED",
                            function=func.__name__,
                            state=self.state,
                        )
                        self._safe_hook(self.on_close, func.__name__)

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
                    inc_circuit_breaker_state(func.__name__, self.OPEN)
                    self.logger.warning(
                        f"Circuit breaker for {func.__name__} transitioned to OPEN due to failure",
                        error=e,
                        function=func.__name__,
                        state=self.state,
                        failure_count=self.failure_count,
                    )
                    self._safe_hook(self.on_open, func.__name__)

            # Re-raise the exception
            raise

    def reset(self) -> None:
        """Reset the circuit breaker to its initial state."""
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.test_calls_remaining = 0
        self.logger.info("Circuit breaker reset to initial state")

    def _safe_hook(self, hook: Callable[[str], None] | None, func_name: str) -> None:
        """Execute a hook safely without propagating errors."""
        if hook is None:
            return
        try:
            hook(func_name)
        except Exception as hook_error:  # pragma: no cover - defensive
            self.logger.warning(
                f"Error in circuit breaker hook for {func_name}: {hook_error}",
                error=hook_error,
                function=func_name,
            )


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

    def __call__(self, func: Callable[Q, T]) -> Callable[Q, T]:
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
        def wrapper(*args: Q.args, **kwargs: Q.kwargs) -> T:
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable[Q, T], *args: Q.args, **kwargs: Q.kwargs) -> T:
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
