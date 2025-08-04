"""Minimal example demonstrating the DearPyGUIBridge."""

import dearpygui.dearpygui as dpg

from devsynth.interface.dpg_bridge import DearPyGUIBridge


def hello_world(*, bridge: DearPyGUIBridge) -> None:
    """Display a simple greeting using the bridge."""
    bridge.display_result("Hello World")


if __name__ == "__main__":
    dpg_bridge = DearPyGUIBridge()
    hello_world(bridge=dpg_bridge)
    dpg.destroy_context()
