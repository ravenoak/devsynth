"""LLM provider utilities."""

from typing import Dict, Any

from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError


# Lazily import provider modules to avoid heavy imports at startup
def get_llm_provider(config: Dict[str, Any] | None = None):
    from .providers import get_llm_provider as _get

    return _get(config)


def factory():
    from .providers import factory as _factory

    return _factory


# Create a logger for this module
logger = DevSynthLogger(__name__)

__all__ = ["factory", "get_llm_provider"]
