from typing import Any, Dict

import pytest

from devsynth.application.agents.validation import ValidationAgent


class _DeterministicAgent(ValidationAgent):
    name = "validation"
    current_role = "validator"

    def get_role_prompt(self) -> str:  # type: ignore[override]
        return "Validation role prompt"

    def create_wsde(self, content: str, content_type: str, metadata: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        return {"content": content, "content_type": content_type, "metadata": metadata}

    def __init__(self, report: str) -> None:
        super().__init__()
        self._report = report

    def generate_text(self, prompt: str) -> str:  # type: ignore[override]
        assert isinstance(prompt, str)
        return self._report


@pytest.mark.fast
@pytest.mark.parametrize(
    "report, expected",
    [
        ("All checks passed; no issues.", True),
        ("An error occurred in module A.", False),  # contains 'error' as a whole word
        ("Exception occurred during run.", False),  # contains 'exception'
        ("Some tests fail on CI.", False),  # contains 'fail' as a whole word
        ("Clean run; everything looks good.", True),
    ],
)
def test_decision_tokens(report: str, expected: bool) -> None:
    """ReqID: FR-VA-01 — ValidationAgent deterministic decision tokens.

    Verifies that whole-word occurrences of 'fail', 'error', or 'exception' in the
    validation report result in is_valid=False; otherwise True.
    """
    agent = _DeterministicAgent(report)
    out = agent.process({})
    assert out["is_valid"] is expected
