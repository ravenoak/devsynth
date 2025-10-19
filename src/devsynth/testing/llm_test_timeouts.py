"""Centralized timeout configuration for LLM provider tests.

Provides environment-variable overrides for CI and local development.
All timeouts are conservative (2-3x measured baseline) to account for
system load on shared hosts.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMTestTimeouts:
    """Timeout configuration for LLM tests."""

    # LM Studio timeouts (conservative: 2-3x measured baseline)
    lmstudio_small: float = 20.0  # Small prompts: 10-50 tokens
    lmstudio_medium: float = 30.0  # Medium prompts: 100-500 tokens
    lmstudio_large: float = 60.0  # Large prompts: 1000+ tokens
    lmstudio_health: float = 10.0  # Health check requests

    # OpenAI/OpenRouter timeouts (faster, cloud-based)
    openai_small: float = 10.0
    openai_medium: float = 15.0
    openai_large: float = 30.0

    # Generic LLM operation timeouts
    generic_call: float = 30.0
    streaming: float = 60.0

    @classmethod
    def from_environment(cls) -> "LLMTestTimeouts":
        """Load timeouts from environment variables with fallback to defaults."""
        return cls(
            lmstudio_small=float(
                os.getenv("DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_SMALL", 20.0)
            ),
            lmstudio_medium=float(
                os.getenv("DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_MEDIUM", 30.0)
            ),
            lmstudio_large=float(
                os.getenv("DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_LARGE", 60.0)
            ),
            lmstudio_health=float(
                os.getenv("DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_HEALTH", 10.0)
            ),
            openai_small=float(os.getenv("DEVSYNTH_TEST_TIMEOUT_OPENAI_SMALL", 10.0)),
            openai_medium=float(os.getenv("DEVSYNTH_TEST_TIMEOUT_OPENAI_MEDIUM", 15.0)),
            openai_large=float(os.getenv("DEVSYNTH_TEST_TIMEOUT_OPENAI_LARGE", 30.0)),
            generic_call=float(os.getenv("DEVSYNTH_TEST_TIMEOUT_GENERIC", 30.0)),
            streaming=float(os.getenv("DEVSYNTH_TEST_TIMEOUT_STREAMING", 60.0)),
        )


# Global singleton for test usage
TEST_TIMEOUTS = LLMTestTimeouts.from_environment()
