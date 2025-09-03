import pytest
from typing import Any, Mapping, Dict

from devsynth.application.agents.validation import ValidationAgent


class FakeValidationAgent(ValidationAgent):
    name = "validation"
    current_role = "validator"

    def get_role_prompt(self) -> str:  # type: ignore[override]
        return "You are a validation expert."

    def generate_text(self, prompt: str) -> str:  # type: ignore[override]
        # Return a deterministic report that indicates success
        assert isinstance(prompt, str)
        return "All checks passed; no failures detected."

    def create_wsde(self, content: str, content_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        return {"content": content, "content_type": content_type, "metadata": metadata}


@pytest.mark.fast
def test_process_returns_typed_output() -> None:
    agent = FakeValidationAgent()
    inputs: Mapping[str, Any] = {
        "context": "Project context",
        "specifications": "Spec details",
        "tests": "Test summary",
        "code": "print('hello')",
    }
    out = agent.process(inputs)

    assert out["is_valid"] is True
    assert isinstance(out["validation_report"], str)
    assert out["agent"] == "validation"
    assert out["role"] == "validator"
    assert isinstance(out["wsde"], dict)


@pytest.mark.fast
def test_get_capabilities_has_defaults_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = FakeValidationAgent()

    def _no_caps() -> list[str]:
        return []

    monkeypatch.setattr(ValidationAgent, "get_capabilities", _no_caps, raising=False)
    # Call the instance method; our monkeypatch forces empty list from super
    caps = FakeValidationAgent().get_capabilities()
    assert "verify_code_against_tests" in caps
