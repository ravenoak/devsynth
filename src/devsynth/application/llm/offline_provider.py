"""Offline LLM provider placeholder."""

from __future__ import annotations

from typing import Any, Dict, List

from .providers import BaseLLMProvider


class OfflineProvider(BaseLLMProvider):
    """Simple offline provider returning deterministic responses."""

    def generate(self, prompt: str, parameters: Dict[str, Any] | None = None) -> str:
        """Return a placeholder response."""
        return f"[offline] {prompt}"

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
    ) -> str:
        """Return a placeholder response using context."""
        return self.generate(prompt, parameters)

    def get_embedding(self, text: str) -> List[float]:
        """Return a dummy embedding."""
        return [0.0] * 3
