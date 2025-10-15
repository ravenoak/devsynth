"""LLM adapter layer for language model integrations.

This package provides adapters for various LLM providers including
OpenAI, LM Studio, and mock implementations for testing.
"""

from .llm_adapter import LLMBackendAdapter, LLMProviderConfig, UnknownLLMProviderError

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

__all__ = [
    "LLMBackendAdapter",
    "LLMProviderConfig",
    "UnknownLLMProviderError",
]
