"""Offline LLM provider for deterministic generation without network access."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List

from ...domain.interfaces.llm import LLMProvider
from ...logging_setup import DevSynthLogger

# These optional dependencies can be expensive to import.  Delay loading them
# until an instance actually requires a model.
torch = None  # type: ignore
AutoModelForCausalLM = None  # type: ignore
AutoTokenizer = None  # type: ignore


def _load_transformer_deps() -> None:
    """Import heavy transformer dependencies lazily."""

    global torch, AutoModelForCausalLM, AutoTokenizer

    # Avoid re-importing if any dependency has already been provided (e.g. via
    # test monkeypatching). Only attempt an import when all are ``None``.
    if (
        torch is not None
        or AutoModelForCausalLM is not None
        or AutoTokenizer is not None
    ):
        return

    try:  # pragma: no cover - optional heavy deps
        import torch as _torch
        from transformers import AutoModelForCausalLM as _AutoModelForCausalLM
        from transformers import AutoTokenizer as _AutoTokenizer

        torch = _torch  # type: ignore
        AutoModelForCausalLM = _AutoModelForCausalLM  # type: ignore
        AutoTokenizer = _AutoTokenizer  # type: ignore
    except Exception:  # pragma: no cover - fallback when deps missing
        torch = None  # type: ignore
        AutoModelForCausalLM = None  # type: ignore
        AutoTokenizer = None  # type: ignore


class OfflineProvider(LLMProvider):
    """Provider that loads a local model or returns deterministic strings."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        provider_cfg = self.config.get("offline_provider", {})
        # Accept both dict and simple string forms. If a string is provided,
        # normalize to a mapping to maintain backward compatibility with
        # earlier configurations/tests that used a simple provider name.
        if isinstance(provider_cfg, str):
            provider_cfg = {"name": provider_cfg}
        self.model_path = provider_cfg.get("model_path") or self.config.get(
            "model_path"
        )
        self.model = None
        self.tokenizer = None

        # Initialize logger
        self.logger = DevSynthLogger("offline_provider")

        if self.model_path:
            _load_transformer_deps()

        if self.model_path and AutoTokenizer and AutoModelForCausalLM:
            try:
                self.logger.info(f"Loading model from {self.model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
                self.logger.info(f"Successfully loaded model from {self.model_path}")
            except Exception as e:
                self.logger.error(
                    f"Failed to load model from {self.model_path}: {str(e)}"
                )
                self.model = None
                self.tokenizer = None

    def generate(self, prompt: str, parameters: dict[str, Any] | None = None) -> str:
        if self.model and self.tokenizer and torch:
            params = parameters or {}
            max_new_tokens = params.get("max_new_tokens", 20)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():  # pragma: no cover - deterministic
                output_ids = self.model.generate(
                    **inputs, max_new_tokens=max_new_tokens, do_sample=False
                )
            return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return f"[offline] {prompt}"

    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
    ) -> str:
        context_text = " ".join(msg.get("content", "") for msg in context)
        combined_prompt = f"{context_text} {prompt}".strip()
        return self.generate(combined_prompt, parameters)

    def get_embedding(self, text: str) -> list[float]:
        digest = sha256(text.encode("utf-8")).digest()
        return [
            int.from_bytes(digest[i : i + 4], "big") / 2**32 for i in range(0, 32, 4)
        ]
