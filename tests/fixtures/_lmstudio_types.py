"""Typed helpers shared by LM Studio fixtures.

These helpers provide a narrow description of the interfaces used by the
fixtures so that mypy can reason about the mocked ``lmstudio`` module without
falling back to ``Any``.  The real SDK exposes a much larger surface area, but
for tests we only need the small subset defined here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict


class LMStudioChatMessage(TypedDict):
    """Single chat message provided to the LM Studio chat completion API."""

    role: str
    content: str


class LMStudioChatPayload(TypedDict):
    """Payload accepted by :meth:`LMStudioLLM.respond`."""

    messages: list[LMStudioChatMessage]


@dataclass(slots=True)
class LMStudioChatCompletion:
    """Simplified representation of a streamed chat completion."""

    content: str


class LMStudioLLM(Protocol):
    """Typed protocol representing the subset of the LM Studio LLM client used."""

    model: str

    def complete(
        self, prompt: str, config: dict[str, object] | None = None
    ) -> LMStudioChatCompletion: ...

    def respond(
        self, payload: LMStudioChatPayload, config: dict[str, object] | None = None
    ) -> LMStudioChatCompletion: ...


class LMStudioEmbeddingModel(Protocol):
    """Protocol describing the embedding model returned by ``lmstudio``."""

    model: str

    def embed(self, text: str) -> list[float]: ...


@dataclass(slots=True)
class LMStudioDownloadedModel:
    """Downloaded model metadata returned by ``lmstudio.sync_api``."""

    model_key: str
    display_name: str


class LMStudioSyncAPI(Protocol):
    """Subset of the LM Studio sync API used during tests."""

    def configure_default_client(self, host: str) -> None: ...

    def list_downloaded_models(self, kind: str) -> list[LMStudioDownloadedModel]: ...

    def _reset_default_client(self) -> None: ...


class LMStudioModule(Protocol):
    """Typed protocol for the dynamic :mod:`lmstudio` module import."""

    def llm(self, model: str) -> LMStudioLLM: ...

    def embedding_model(self, model: str) -> LMStudioEmbeddingModel: ...

    sync_api: LMStudioSyncAPI
