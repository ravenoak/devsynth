"""
Web UI module for DevSynth.

This module provides web interface components for DevSynth.
"""

from .rendering import LifecyclePages, OperationsPages, PageRenderer, ProjectSetupPages, SupportPages
from .rendering_simulation import simulate_progress_rendering

# WebUI is likely defined in a main webui.py file that doesn't exist yet
# For now, create a placeholder
class WebUI:
    """Main WebUI class for DevSynth."""
    pass

__all__ = [
    "LifecyclePages",
    "OperationsPages",
    "PageRenderer",
    "ProjectSetupPages",
    "SupportPages",
    "simulate_progress_rendering",
    "WebUI",
]
