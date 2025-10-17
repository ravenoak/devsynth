"""
Web UI module for DevSynth.

This module provides web interface components for DevSynth.
"""

from .rendering import LifecyclePages, OperationsPages, PageRenderer, ProjectSetupPages, SupportPages
from .rendering_simulation import simulate_progress_rendering
from .routing import Router

# Import WebUI class from the main webui module, but handle import errors gracefully
try:
    from devsynth.interface.webui import WebUI  # type: ignore
except ImportError:
    # WebUI class might not be available if Streamlit is not installed
    WebUI = None

__all__ = [
    "LifecyclePages",
    "OperationsPages",
    "PageRenderer",
    "ProjectSetupPages",
    "Router",
    "SupportPages",
    "simulate_progress_rendering",
    "WebUI",
]
