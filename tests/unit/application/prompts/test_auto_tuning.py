import pytest
from devsynth.application.prompts.auto_tuning import BasicPromptTuner
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from tests.fixtures.ports import llm_port


def test_temperature_adjustment():
    tuner = BasicPromptTuner()
    base = tuner.parameters()["temperature"]
    tuner.adjust(success=True)
    assert tuner.parameters()["temperature"] < base
    tuner.adjust(success=False)
    assert tuner.parameters()["temperature"] >= base


def test_unified_agent_uses_tuner(llm_port):
    agent = UnifiedAgent()
    config = AgentConfig(name="ua", agent_type=AgentType.ORCHESTRATOR, description="", capabilities=[])
    agent.initialize(config)
    agent.set_llm_port(llm_port)

    captured = {}

    def fake_generate(prompt, parameters=None, provider_type=None):
        captured["params"] = parameters
        return "ok"

    llm_port.generate = fake_generate

    agent.generate_text("hi")
    first_temp = captured["params"]["temperature"]
    agent.record_prompt_feedback(success=False)
    agent.generate_text("hi again")
    second_temp = captured["params"]["temperature"]
    assert second_temp > first_temp
