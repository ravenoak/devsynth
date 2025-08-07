"""Launch the Dear PyGUI interface."""

from __future__ import annotations

from typing import Optional

from devsynth.config import get_settings
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _resolve_bridge

try:  # pragma: no cover - optional dependency handling
    from devsynth.interface.dpg_ui import run as run_dpg_ui
except Exception:  # pragma: no cover - defensive
    run_dpg_ui = None  # type: ignore


def dpg_cmd(*, bridge: Optional[UXBridge] = None) -> None:
    """Launch the Dear PyGUI interface."""
    bridge = _resolve_bridge(bridge)
    settings = get_settings(reload=True)
    if not getattr(settings, "gui_enabled", False):
        bridge.display_result(
            "[yellow]GUI support is disabled. Enable 'gui.enabled' in configuration to use this command.[/yellow]"
        )
        return
    try:
        if run_dpg_ui is None:
            raise ImportError("Dear PyGUI interface is unavailable")
        run_dpg_ui()
    except Exception as err:  # pragma: no cover - defensive
        bridge.display_result(f"[red]Error:[/red] {err}")


__all__ = ["dpg_cmd"]
