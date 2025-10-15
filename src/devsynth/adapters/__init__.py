"""Adapter layer for external integrations.

This package provides adapters for external services and integrations
including LLM providers, issue trackers, and memory backends.
"""

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Note: Adapter classes are imported from submodules to avoid heavy dependencies
# at package import time. Import specific adapters as needed.
