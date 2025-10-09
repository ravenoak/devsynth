"""Typed helpers for simulating WebUI rendering without Streamlit."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from typing import Any, Protocol, TypeAlias, TypedDict

from devsynth.interface.streamlit_contracts import StreamlitModule
from devsynth.interface.ux_bridge import sanitize_output

EventPayload: TypeAlias = Mapping[str, Any]
RenderEvent: TypeAlias = tuple[str, EventPayload]


class SimulationResult(TypedDict):
    """Structured payload describing a deterministic render run."""

    events: tuple[RenderEvent, ...]
    streamlit: StreamlitModule


class ProgressSimulationHost(Protocol):
    """Contract implemented by renderers used in progress simulations."""

    streamlit: StreamlitModule

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None: ...

    def _render_progress_summary(
        self,
        summary: Mapping[str, Any],
        *,
        container: Any | None = None,
    ) -> None: ...


def simulate_progress_rendering(
    pages: ProgressSimulationHost,
    summary: Mapping[str, Any],
    *,
    container: Any | None = None,
    errors: Sequence[object] | None = None,
    clock: Callable[[], float] | None = None,
) -> SimulationResult:
    """Render a deterministic progress summary without a Streamlit runtime."""

    events: list[RenderEvent] = []

    with ExitStack() as stack:
        if clock is not None:
            original_time = time.time

            def _restore_time() -> None:
                time.time = original_time

            stack.callback(_restore_time)
            time.time = clock

        pages._render_progress_summary(summary, container=container)
        events.append(
            (
                "summary",
                {
                    "description": sanitize_output(str(summary.get("description", ""))),
                },
            )
        )

        if errors:
            for raw in errors:
                message = sanitize_output(str(raw))
                pages.display_result(message, message_type="error", highlight=False)
                events.append(("error", {"message": message}))

    return {"events": tuple(events), "streamlit": pages.streamlit}


__all__ = [
    "simulate_progress_rendering",
    "SimulationResult",
    "ProgressSimulationHost",
]
