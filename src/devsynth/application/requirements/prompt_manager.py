"""Compatibility module for prompt management.

This module provides backward compatibility by exposing the
``PromptManager`` class from the prompts package under the
``devsynth.application.requirements`` namespace.
"""

from devsynth.application.prompts.prompt_manager import PromptManager

__all__ = ["PromptManager"]
