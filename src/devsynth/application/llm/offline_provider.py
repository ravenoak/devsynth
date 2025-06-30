"""Offline LLM provider using a small local model."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class BaseLLMProvider:
    """Minimal base class for LLM providers."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def generate(self, prompt: str, parameters: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError

    def get_embedding(self, text: str) -> List[float]:
        raise NotImplementedError


class OfflineProvider(BaseLLMProvider):
    """Provider that loads a local model for deterministic generation."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        provider_cfg = self.config.get("offline_provider", {})
        self.model_path = provider_cfg.get("model_path") or self.config.get(
            "model_path"
        )
        self.model = None
        self.tokenizer = None
        if self.model_path:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)

    def generate(self, prompt: str, parameters: Dict[str, Any] | None = None) -> str:
        if self.model and self.tokenizer:
            params = parameters or {}
            max_new_tokens = params.get("max_new_tokens", 20)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs, max_new_tokens=max_new_tokens, do_sample=False
                )
            return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return f"[offline] {prompt}"

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
    ) -> str:
        context_text = " ".join(msg.get("content", "") for msg in context)
        combined_prompt = f"{context_text} {prompt}".strip()
        return self.generate(combined_prompt, parameters)

    def get_embedding(self, text: str) -> List[float]:
        digest = sha256(text.encode("utf-8")).digest()
        return [
            int.from_bytes(digest[i : i + 4], "big") / 2**32 for i in range(0, 32, 4)
        ]
