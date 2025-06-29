"""LLM provider utilities."""

from typing import Dict, Any

from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

from .providers import factory, get_llm_provider

# Import providers so they are registered
from . import local_provider  # noqa: F401
from . import offline_provider  # noqa: F401

# Create a logger for this module
logger = DevSynthLogger(__name__)

__all__ = ["factory", "get_llm_provider"]
