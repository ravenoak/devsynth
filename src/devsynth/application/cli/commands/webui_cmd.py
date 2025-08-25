"""[experimental] Launch the Streamlit WebUI.

This command depends on optional extras and may not be available in all environments.
"""

from __future__ import annotations

from typing import Optional

from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.webui import run

from ..utils import _resolve_bridge


def webui_cmd(*, bridge: Optional[UXBridge] = None) -> None:
    """Launch the Streamlit WebUI."""
    bridge = _resolve_bridge(bridge)
    try:
        run()
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}")


__all__ = ["webui_cmd"]
