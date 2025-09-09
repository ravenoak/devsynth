from unittest.mock import MagicMock

import pytest

from devsynth.application.agents.validation import ValidationAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


@pytest.fixture
def agent_with_llm():
    agent = ValidationAgent()
    cfg = AgentConfig(
        name="TestValidationAgent",
        agent_type=AgentType.VALIDATION,
        description="Test Validation Agent",
        capabilities=[],
    )
    agent.initialize(cfg)
    mock_port = MagicMock(spec=LLMPort)
    agent.set_llm_port(mock_port)
    return agent, mock_port


@pytest.mark.fast
def test_process_affirmative_is_valid_true(agent_with_llm):
    """ReqID: FR-VA-01 Ensure affirmative language yields is_valid=True."""
    agent, port = agent_with_llm
    port.generate.return_value = "All checks passed. No errors detected."
    out = agent.process({"context": "ctx", "code": "print('ok')"})
    port.generate.assert_called_once()
    assert out["is_valid"] is True
    assert "validation_report" in out
    assert out["wsde"].metadata["type"] == "validation_report"


@pytest.mark.fast
def test_process_failure_tokens_set_invalid(agent_with_llm):
    """ReqID: FR-VA-02 Flag whole-word failure tokens (fail|error|exception)."""
    agent, port = agent_with_llm
    port.generate.return_value = "Tests fail due to exception in module."
    out = agent.process({})
    assert out["is_valid"] is False


@pytest.mark.fast
def test_process_neutral_text_is_valid(agent_with_llm):
    """ReqID: FR-VA-03 Neutral text without failure tokens yields True."""
    agent, port = agent_with_llm
    port.generate.return_value = "Review complete. Looks good overall."
    out = agent.process({})
    assert out["is_valid"] is True


@pytest.mark.fast
def test_is_valid_word_boundary_only(agent_with_llm):
    """ReqID: FR-VA-04 'failures' should not trip whole-word 'fail' check."""
    agent, port = agent_with_llm
    # contains the word 'failures' but not whole-word 'fail'
    port.generate.return_value = "There were 0 failures reported."
    out = agent.process({})
    assert out["is_valid"] is True


@pytest.mark.fast
def test_wsde_contains_agent_and_role(agent_with_llm):
    """ReqID: FR-VA-05 WSDE/role metadata preserved and exposed in output."""
    agent, port = agent_with_llm
    agent.current_role = "Evaluator"
    port.generate.return_value = "No issues."
    out = agent.process({})
    wsde = out["wsde"]
    assert wsde.metadata["agent"] == "TestValidationAgent"
    assert out["role"] == "Evaluator"
