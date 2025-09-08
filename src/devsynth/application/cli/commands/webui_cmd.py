"""[experimental] Launch the Streamlit WebUI.

This command depends on optional extras and may not be available in all environments.
"""

from __future__ import annotations

from typing import Optional

from devsynth.exceptions import DevSynthError
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _resolve_bridge


def webui_cmd(*, bridge: UXBridge | None = None) -> None:
    """Launch the Streamlit WebUI.

    Notes:
        - This command requires the optional web UI dependencies. To install:
          `poetry install --with dev --extras webui` or equivalent.
        - Implemented with a lazy import so that the main CLI remains importable
          in minimal environments (no Streamlit installed), per project guidelines.
    """
    bridge = _resolve_bridge(bridge)
    try:
        # Lazy import to avoid importing Streamlit unless the command is invoked.
        from devsynth.interface.webui import run  # type: ignore

        run()
    except (
        ModuleNotFoundError,
        DevSynthError,
    ) as err:  # pragma: no cover - optional dep missing
        bridge.display_result(
            "[yellow]WebUI dependencies are not installed.[/yellow]\n"
            "Install optional extras and retry, e.g.:\n"
            "  poetry install --with dev --extras webui\n"
            f"Details: {err}"
        )
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}")


__all__ = ["webui_cmd"]
