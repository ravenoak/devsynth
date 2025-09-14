"""Testing utilities for DevSynth.

The :mod:`devsynth.testing` package exposes helpers and prompt templates that
assist with generating and running tests for DevSynth modules.
"""

from .prompts import INTEGRATION_TEST_PROMPT

__all__: list[str] = ["INTEGRATION_TEST_PROMPT"]
