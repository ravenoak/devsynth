from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.application.agents.test import TestAgent
from devsynth.domain.models.agent import AgentConfig, AgentType


@pytest.mark.fast
def test_process_scaffolds_tests_from_context(tmp_path: Path) -> None:
    """TestAgent derives integration tests from project context.

    ReqID: N/A"""

    agent = TestAgent()
    agent.generate_text = MagicMock(return_value="tests")
    agent.create_wsde = MagicMock(return_value="wsde")
    config = AgentConfig(
        name="TestAgent",
        agent_type=AgentType.ORCHESTRATOR,
        description="Test agent",
        capabilities=[],
    )
    agent.initialize(config)

    context = "The payment service communicates with the inventory module."
    result = agent.process({"context": context, "integration_output_dir": tmp_path})

    assert "test_payment.py" in result["integration_tests"]
    assert "test_inventory.py" in result["integration_tests"]
    assert (tmp_path / "test_payment.py").exists()
    assert (tmp_path / "test_inventory.py").exists()
