"""Unit tests covering research persona specifications."""

from __future__ import annotations

import pytest

from devsynth.domain.models.wsde_roles import (
    ResearchPersonaSpec,
    enumerate_research_personas,
    resolve_research_persona,
)


@pytest.mark.fast
def test_enumerate_research_personas_includes_overlays() -> None:
    """Expanded persona roster should be discoverable via enumeration."""

    personas = enumerate_research_personas()
    display_names = {spec.display_name for spec in personas}

    expected = {
        "Research Lead",
        "Bibliographer",
        "Synthesist",
        "Synthesizer",
        "Contrarian",
        "Fact Checker",
        "Planner",
        "Moderator",
    }

    assert display_names == expected


@pytest.mark.fast
@pytest.mark.parametrize(
    "persona_name",
    [
        "Synthesizer",
        "Contrarian",
        "Fact Checker",
        "Planner",
        "Moderator",
    ],
)
def test_persona_payload_exposes_overlay_metadata(persona_name: str) -> None:
    """Overlay personas must provide telemetry metadata when enabled."""

    spec = resolve_research_persona(persona_name)
    assert isinstance(spec, ResearchPersonaSpec)

    payload = spec.as_payload()
    assert payload["name"] == persona_name
    assert payload["capabilities"], "Capabilities should not be empty"
    assert payload.get("prompt_template"), "Prompt template must be recorded"
    assert payload.get("fallback_behavior"), "Fallback behavior must be recorded"
    assert payload.get("success_criteria"), "Success criteria must be recorded"
