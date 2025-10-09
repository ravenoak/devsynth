"""Dialectical reasoning loop utilities for EDRR workflows.

The implementation enforces strict typing for consistent static analysis.

Proof of convergence and invariants:
    docs/implementation/reasoning_loop_invariants.md
Issue: issues/Finalize-dialectical-reasoning.md
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Any

from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.domain.models.wsde_dialectical_types import (
    DialecticalTask,
)
from devsynth.domain.models.wsde_dialectical_types import (
    apply_dialectical_reasoning as typed_apply,
)
from devsynth.domain.models.wsde_dialectical_types import (
    ensure_dialectical_task,
)
from devsynth.exceptions import ConsensusError
from devsynth.logging_setup import DevSynthLogger

from ..base import Phase
from .contracts import (
    EDRRCoordinatorProtocol,
    MemoryIntegration,
    WSDETeamProtocol,
)

logger = DevSynthLogger(__name__)


ApplyDialecticalReasoning = Callable[
    [WSDETeamProtocol, DialecticalTask, Any, MemoryIntegration | None],
    DialecticalSequence,
]


def _import_apply_dialectical_reasoning() -> ApplyDialecticalReasoning:
    """Return the dialectical reasoning callable.

    Extracted for tests so that monkeypatching this module-local accessor swaps
    the underlying reasoning implementation without touching global state.
    """

    return typed_apply


def reasoning_loop(
    wsde_team: WSDETeamProtocol,
    task: DialecticalTask | Mapping[str, Any],
    critic_agent: Any,
    memory_integration: MemoryIntegration | None = None,
    *,
    phase: Phase = Phase.REFINE,
    max_iterations: int = 3,
    coordinator: EDRRCoordinatorProtocol | None = None,
    retry_attempts: int = 1,
    retry_backoff: float = 0.05,
    deterministic_seed: int | None = None,
    max_total_seconds: float | None = None,
) -> list[DialecticalSequence]:
    """Iteratively apply dialectical reasoning until completion or failure.

    Improvements:
    - Align coordinator recording with the actual EDRR phase returned by the
      dialectical reasoning step when available.
    - Advance the phase deterministically between iterations using either the
      provided `next_phase` from results or a stable transition map.
    - Add lightweight retries for transient errors (excluding ConsensusError).
    - Add deterministic seeding and an optional total time budget for tests.
    """
    # Optional deterministic seeding for tests
    if deterministic_seed is not None:
        try:
            import random

            random.seed(deterministic_seed)
        except Exception:
            pass
        try:  # numpy is optional; seed if available
            import importlib

            numpy_random = importlib.import_module("numpy.random")
            numpy_random.seed(deterministic_seed)
        except Exception:
            pass

    start_time = time.monotonic()

    results: list[Mapping[str, Any]] = []
    current_task: DialecticalTask = ensure_dialectical_task(task)
    current_phase: Phase = phase

    # Deterministic fallback transition map (keeps refine idempotent by default)
    phase_transition: dict[Phase, Phase] = {
        Phase.EXPAND: Phase.DIFFERENTIATE,
        Phase.DIFFERENTIATE: Phase.REFINE,
        Phase.REFINE: Phase.REFINE,
    }

    for iteration in range(max_iterations):
        # Enforce total time budget if configured
        if (
            max_total_seconds is not None
            and (time.monotonic() - start_time) >= max_total_seconds
        ):
            logger.debug("reasoning_loop exiting due to max_total_seconds budget")
            break

        logger.info("Dialectical reasoning iteration %s", iteration + 1)

        # Inner retry loop for transient exceptions
        result: DialecticalSequence | Mapping[str, Any] | None = None
        stop = False
        attempts = 0
        apply_dialectical_reasoning: ApplyDialecticalReasoning = (
            _import_apply_dialectical_reasoning()
        )
        while True:
            try:
                result = apply_dialectical_reasoning(
                    wsde_team, current_task, critic_agent, memory_integration
                )
                break
            except ConsensusError as exc:  # pragma: no cover - logging path
                if coordinator is not None:
                    coordinator.record_consensus_failure(exc)
                else:
                    logger.error("Consensus failure", exc_info=exc)
                stop = True
                break
            except Exception:
                if attempts < retry_attempts:
                    # Exponential backoff, but respect remaining budget
                    sleep_for = retry_backoff * (2**attempts)
                    if max_total_seconds is not None:
                        remaining = max(
                            0.0, max_total_seconds - (time.monotonic() - start_time)
                        )
                        if remaining <= 0:
                            stop = True
                            break
                        sleep_for = min(sleep_for, remaining)
                    logger.debug(
                        "Transient error in reasoning step; retrying in %ss",
                        sleep_for,
                        exc_info=True,
                    )
                    time.sleep(sleep_for)
                    attempts += 1
                    continue
                # Give up after exhausting retries; log and stop the loop
                logger.debug(
                    "Giving up after retries due to transient errors", exc_info=True
                )
                stop = True
                break

        if stop or result is None:
            break

        append_result: Mapping[str, Any]
        if isinstance(result, DialecticalSequence):
            result_mapping = result
            append_result = result
        elif isinstance(result, Mapping):
            result_mapping = result
            append_result = dict(result)
        else:
            raise TypeError("apply_dialectical_reasoning must return a mapping payload")

        # Determine the effective phase for recording from result payload
        effective_phase = current_phase
        result_phase_value = result_mapping.get("phase")
        if isinstance(result_phase_value, str):
            try:
                effective_phase = Phase(result_phase_value.lower())
            except Exception:
                # Ignore unknown phases and keep current_phase
                pass

        if coordinator is not None:
            record_map: dict[Phase, Callable[[dict[str, Any]], dict[str, Any]]] = {
                Phase.EXPAND: coordinator.record_expand_results,
                Phase.DIFFERENTIATE: coordinator.record_differentiate_results,
                Phase.REFINE: coordinator.record_refine_results,
            }
            record_map.get(effective_phase, coordinator.record_refine_results)(
                dict(result_mapping)
            )

        results.append(append_result)

        # Stop condition if the reasoning reports completion
        if result_mapping.get("status") == "completed":
            break

        # Prepare next iteration inputs
        synthesis = result_mapping.get("synthesis")
        if synthesis is not None:
            current_task = current_task.with_solution(synthesis)

        # Advance phase for the next iteration, honoring result.next_phase when provided
        next_phase_value = result_mapping.get("next_phase")
        if isinstance(next_phase_value, str):
            try:
                current_phase = Phase(next_phase_value.lower())
            except Exception:
                current_phase = phase_transition.get(current_phase, current_phase)
        else:
            current_phase = phase_transition.get(current_phase, current_phase)

    return results
