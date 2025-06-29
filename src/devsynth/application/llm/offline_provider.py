"""Offline LLM provider placeholder."""

from __future__ import annotations

from typing import Any, Dict, List
from hashlib import sha256

from .providers import BaseLLMProvider


class OfflineProvider(BaseLLMProvider):
    """Simple offline provider returning deterministic responses."""

    def generate(self, prompt: str, parameters: Dict[str, Any] | None = None) -> str:
        """Return a deterministic response for the given prompt."""
        return f"[offline] {prompt}"

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
    ) -> str:
        """Return a deterministic response using conversation context."""
        context_text = " ".join(msg.get("content", "") for msg in context)
        combined_prompt = f"{context_text} {prompt}".strip()
        return self.generate(combined_prompt, parameters)

    def get_embedding(self, text: str) -> List[float]:
        """Return a deterministic embedding vector for the text."""
        digest = sha256(text.encode("utf-8")).digest()
        return [int.from_bytes(digest[i : i + 4], "big") / 2**32 for i in range(0, 32, 4)]
