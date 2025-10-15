"""Interface layer for DevSynth user interactions.

This package provides the core interfaces and bridges for user interaction
across different UI frameworks (CLI, WebUI, Agent API).
"""

from .ux_bridge import ProgressIndicator, UXBridge, sanitize_output

# Import CLI components
from .cli import CLIUXBridge

# Import WebUI directly from the webui module to avoid circular imports
try:
    import sys
    from pathlib import Path
    import importlib.util

    # Load the webui.py module directly
    webui_path = Path(__file__).parent / "webui.py"
    spec = importlib.util.spec_from_file_location("devsynth.interface.webui_module", webui_path)
    if spec and spec.loader:
        webui_module = importlib.util.module_from_spec(spec)
        sys.modules["devsynth.interface.webui_module"] = webui_module
        spec.loader.exec_module(webui_module)
        WebUI = webui_module.WebUI
    else:
        WebUI = None
except (ImportError, AttributeError, Exception):
    # Fallback if webui module has issues
    WebUI = None

__all__ = [
    "CLIUXBridge",
    "ProgressIndicator",
    "UXBridge",
    "WebUI",
    "sanitize_output",
]
