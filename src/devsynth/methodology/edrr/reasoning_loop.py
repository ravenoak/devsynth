"""Dialectical reasoning loop utilities for EDRR workflows.

NOTE (mypy override): This module currently has relaxed mypy settings per
pyproject.toml [tool.mypy.overrides] while the API is stabilizing.
TODO(typing): Re-enable disallow_untyped_defs and check_untyped_defs once
signatures and coordinator interactions are fully typed. Target: 2025-10-01. See docs/tasks.md (Static analysis).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from devsynth.domain.models.wsde_dialectical import (
    apply_dialectical_reasoning as _apply_dialectical_reasoning,
)
from devsynth.exceptions import ConsensusError
from devsynth.logger import log_consensus_failure
from devsynth.logging_setup import DevSynthLogger

from ..base import Phase

if TYPE_CHECKING:  # avoid runtime circular imports
    from .coordinator import EDRRCoordinator

logger = DevSynthLogger(__name__)


def reasoning_loop(
    wsde_team: Any,
    task: Dict[str, Any],
    critic_agent: Any,
    memory_integration: Optional[Any] = None,
    *,
    phase: Phase = Phase.REFINE,
    max_iterations: int = 3,
    coordinator: Optional[EDRRCoordinator] = None,
    retry_attempts: int = 1,
    retry_backoff: float = 0.05,
    deterministic_seed: Optional[int] = None,
    max_total_seconds: Optional[float] = None,
) -> List[Dict[str, Any]]:
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
            import numpy as np  # type: ignore

            np.random.seed(deterministic_seed)  # type: ignore[attr-defined]
        except Exception:
            pass

    start_time = time.monotonic()

    results: List[Dict[str, Any]] = []
    current_task = task
    current_phase: Phase = phase

    # Deterministic fallback transition map (keeps refine idempotent by default)
    phase_transition = {
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
        result: Optional[Dict[str, Any]] = None
        stop = False
        attempts = 0
        while True:
            try:
                result = _apply_dialectical_reasoning(
                    wsde_team, current_task, critic_agent, memory_integration
                )
                break
            except ConsensusError as exc:  # pragma: no cover - logging path
                if coordinator is not None:
                    coordinator.record_consensus_failure(exc)
                else:
                    log_consensus_failure(logger, exc)
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

        # Determine the effective phase for recording from result payload
        effective_phase = current_phase
        result_phase_value = result.get("phase")
        if isinstance(result_phase_value, str):
            try:
                effective_phase = Phase(result_phase_value.lower())
            except Exception:
                # Ignore unknown phases and keep current_phase
                pass

        if coordinator is not None:
            record_map = {
                Phase.EXPAND: coordinator.record_expand_results,
                Phase.DIFFERENTIATE: coordinator.record_differentiate_results,
                Phase.REFINE: coordinator.record_refine_results,
            }
            record_map.get(effective_phase, coordinator.record_refine_results)(result)

        results.append(result)

        # Stop condition if the reasoning reports completion
        if result.get("status") == "completed":
            break

        # Prepare next iteration inputs
        synthesis = result.get("synthesis")
        if synthesis is not None:
            current_task = {**current_task, "solution": synthesis}

        # Advance phase for the next iteration, honoring result.next_phase when provided
        next_phase_value = result.get("next_phase")
        if isinstance(next_phase_value, str):
            try:
                current_phase = Phase(next_phase_value.lower())
            except Exception:
                current_phase = phase_transition.get(current_phase, current_phase)
        else:
            current_phase = phase_transition.get(current_phase, current_phase)

    return results
