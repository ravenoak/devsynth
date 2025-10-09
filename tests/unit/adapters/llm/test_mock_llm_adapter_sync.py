"""Synchronous coverage for the typed MockLLMAdapter."""

from __future__ import annotations

import sys
import types
from dataclasses import asdict
from typing import Mapping

import pytest

# Provide lightweight stubs so importing MockLLMAdapter does not pull heavy runtime dependencies.
if "devsynth.application.llm.providers" not in sys.modules:
    providers_module = types.ModuleType("devsynth.application.llm.providers")

    class _StubBaseLLMProvider:
        def __init__(self, config: Mapping[str, object] | None = None) -> None:
            self.config = dict(config or {})

    providers_module.BaseLLMProvider = _StubBaseLLMProvider  # type: ignore[attr-defined]
    parent_pkg = sys.modules.setdefault(
        "devsynth.application.llm", types.ModuleType("devsynth.application.llm")
    )
    setattr(parent_pkg, "providers", providers_module)
    sys.modules["devsynth.application.llm.providers"] = providers_module

if "devsynth.domain.interfaces.llm" not in sys.modules:
    interfaces_module = types.ModuleType("devsynth.domain.interfaces.llm")

    class _StubStreamingLLMProvider:
        pass

    class _StubLLMProvider:
        pass

    class _StubLLMProviderFactory:
        pass

    interfaces_module.StreamingLLMProvider = _StubStreamingLLMProvider  # type: ignore[attr-defined]
    interfaces_module.LLMProvider = _StubLLMProvider  # type: ignore[attr-defined]
    interfaces_module.LLMProviderFactory = _StubLLMProviderFactory  # type: ignore[attr-defined]
    sys.modules["devsynth.domain.interfaces.llm"] = interfaces_module

from devsynth.adapters.llm.mock_llm_adapter import (
    DEFAULT_RESPONSE_TEXT,
    MockLLMAdapter,
    MockLLMConfig,
    MockResponseTemplate,
)


@pytest.mark.fast
def test_mock_response_template_serializes() -> None:
    """Ensure response templates serialize predictably for coverage docs."""

    template = MockResponseTemplate(key="alpha", text="Alpha response")

    assert asdict(template) == {"key": "alpha", "text": "Alpha response"}


@pytest.mark.fast
def test_config_round_trip_preserves_defaults() -> None:
    """Serialising then rebuilding a config should preserve typed payloads."""

    config = MockLLMConfig()
    raw = config.to_raw_config()

    rebuilt = MockLLMConfig.from_mapping(raw)
    rebuilt_responses = {
        template.key: template.text for template in rebuilt.response_templates
    }

    assert rebuilt.default_response == config.default_response
    assert rebuilt_responses["code_review"].startswith("I've reviewed the code")
    assert rebuilt.default_embedding == pytest.approx(config.default_embedding)


@pytest.mark.fast
def test_generate_matches_custom_template() -> None:
    """Custom template keys should steer prompt matching without Any casts."""

    config = MockLLMConfig(
        default_response="fallback",
        response_templates=(MockResponseTemplate(key="special", text="special reply"),),
    )
    adapter = MockLLMAdapter(config)

    assert adapter.generate("this is a special prompt") == "special reply"


@pytest.mark.fast
def test_generate_uses_default_when_no_template_matches() -> None:
    """The adapter should fall back to the typed default response."""

    config = MockLLMConfig(
        default_response="typed default",
        response_templates=(
            MockResponseTemplate(key="code_review", text="diagnostic"),
        ),
    )
    adapter = MockLLMAdapter(config)

    assert adapter.generate("no match present") == "typed default"


@pytest.mark.fast
def test_config_from_mapping_coerces_sequences() -> None:
    """Numeric sequences from mappings should coerce into typed templates."""

    mapping = {
        "default_response": "configured default",
        "responses": {"special": "handled"},
        "default_embedding": [1, 2, 3],
        "embeddings": {"special": [4, 5]},
    }

    config = MockLLMConfig.from_mapping(mapping)

    response_map = {
        template.key: template.text for template in config.response_templates
    }
    embedding_map = {
        template.key: list(template.vector) for template in config.embedding_templates
    }

    assert response_map == {"special": "handled"}
    assert embedding_map == {"special": [4.0, 5.0]}
    assert list(config.default_embedding) == [1.0, 2.0, 3.0]


@pytest.mark.fast
def test_config_from_mapping_falls_back_to_defaults() -> None:
    """Invalid sections should trigger default templates and embeddings."""

    config = MockLLMConfig.from_mapping({"responses": {"unsupported": 123}})

    response_keys = {template.key for template in config.response_templates}
    assert {"default", "code_review"}.issubset(response_keys)


@pytest.mark.fast
def test_adapter_initialises_from_mapping() -> None:
    """Mapping input should hydrate the dataclass model and raw config."""

    adapter = MockLLMAdapter(
        {"responses": {"demo": "value"}, "embeddings": {"demo": [0]}}
    )

    assert adapter.config_model.default_response == DEFAULT_RESPONSE_TEXT
    assert adapter.responses["demo"] == "value"
    assert adapter.get_embedding("demo text") == [0.0]


class ErroringMockAdapter(MockLLMAdapter):
    """Adapter that deliberately fails for streaming error propagation checks."""

    def generate(
        self, prompt: str, parameters: Mapping[str, object] | None = None
    ) -> str:
        raise RuntimeError("generate failed")


@pytest.mark.fast
@pytest.mark.asyncio
async def test_generate_stream_propagates_generate_failure() -> None:
    """If generate raises, awaiting the stream coroutine should bubble the error."""

    adapter = ErroringMockAdapter()

    with pytest.raises(RuntimeError, match="generate failed"):
        await adapter.generate_stream("any prompt")
