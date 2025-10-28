"""Run the DevSynth API server."""

from __future__ import annotations

from typing import Optional

from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import configure_logging

from ..utils import _resolve_bridge


def serve_cmd(
    host: str = "0.0.0.0",  # nosec B104: default open binding for developer convenience
    port: int = 8000,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Run the DevSynth API server.

    Example:
        `devsynth serve --host 127.0.0.1 --port 8080`
    """
    bridge = _resolve_bridge(bridge)
    try:
        configure_logging()
        import uvicorn

        uvicorn.run("devsynth.api:app", host=host, port=port, log_level="info")
    except ImportError:  # pragma: no cover - optional dependency
        bridge.display_result(
            "[red]Serve command requires the 'uvicorn' package. "
            "Install it with 'pip install uvicorn' or use the dev extras.[/red]",
            highlight=False,
        )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


__all__ = ["serve_cmd"]
