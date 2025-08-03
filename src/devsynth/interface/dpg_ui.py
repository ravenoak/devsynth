"""Dear PyGUI based interface for DevSynth workflows.

This module wires the :class:`DearPyGUIBridge` into a minimal window
providing quick access to common DevSynth CLI workflows.  Each button
invokes the corresponding workflow function through the bridge which
ensures consistent user interaction behaviour across interfaces.
"""
from __future__ import annotations

from typing import Callable

try:  # pragma: no cover - optional dependency
    import dearpygui.dearpygui as dpg
except Exception:  # pragma: no cover - defensive
    dpg = None  # type: ignore

from .dpg_bridge import DearPyGUIBridge


def _bind(cmd: Callable[[DearPyGUIBridge], None], bridge: DearPyGUIBridge) -> Callable[[], None]:
    """Return a callback that executes *cmd* with the provided bridge."""

    def _callback() -> None:
        cmd(bridge=bridge)

    return _callback


def run() -> None:
    """Launch the Dear PyGUI interface."""
    if dpg is None:  # pragma: no cover - defensive
        raise RuntimeError("dearpygui is required for the DPG interface")

    bridge = DearPyGUIBridge()

    # Import workflow commands lazily to avoid heavy dependencies at import time
    from devsynth.application.cli import init_cmd, gather_cmd, inspect_cmd

    with dpg.window(label="DevSynth", tag="__primary_window"):
        dpg.add_button(label="Init", callback=_bind(init_cmd, bridge))
        dpg.add_button(label="Gather", callback=_bind(gather_cmd, bridge))
        dpg.add_button(label="Inspect", callback=_bind(inspect_cmd, bridge))

    dpg.set_primary_window("__primary_window", True)
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


__all__ = ["run"]
