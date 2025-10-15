"""Application layer for DevSynth core functionality.

This package contains the main application logic including CLI commands,
agents, memory management, and workflow orchestration.
"""

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Note: Individual submodules are imported lazily to avoid circular dependencies
# and expensive imports at package level. Use explicit imports when needed.

# Import CLI module to make it available
from . import cli
