import pytest
from devsynth.application.prompts.auto_tuning import (
    BasicPromptTuner,
    PromptAutoTuner,
    PromptVariant,
    iterative_prompt_adjustment,
    run_tuning_iteration,
)
from unittest.mock import patch
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType


class _DummyLLMPort:

    def __init__(self):
        self.generate = lambda prompt, parameters=None, provider_type=None: "ok"


@pytest.fixture
def llm_port():
    return _DummyLLMPort()


def test_temperature_adjustment_succeeds():
    """Test that temperature adjustment succeeds.

    ReqID: N/A"""
    tuner = BasicPromptTuner()
    base = tuner.parameters()["temperature"]
    tuner.adjust(success=True)
    assert tuner.parameters()["temperature"] < base
    tuner.adjust(success=False)
    assert tuner.parameters()["temperature"] >= base


def test_unified_agent_uses_tuner_succeeds(llm_port):
    """Test that unified agent uses tuner succeeds.

    ReqID: N/A"""
    agent = UnifiedAgent()
    config = AgentConfig(
        name="ua", agent_type=AgentType.ORCHESTRATOR, description="", capabilities=[]
    )
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


def test_run_tuning_iteration_records_feedback_succeeds():
    """Test that run tuning iteration records feedback succeeds.

    ReqID: N/A"""
    tuner = PromptAutoTuner()
    tuner.register_template("test", "base")

    def evaluate(_prompt: str) -> float:
        return 0.6

    variant = run_tuning_iteration(tuner, "test", evaluate)
    assert variant.performance_score > 0
    assert tuner.prompt_variants["test"][0].usage_count >= 1


def test_iterative_prompt_adjustment_returns_best_variant_succeeds():
    """Test that iterative prompt adjustment returns best variant succeeds.

    ReqID: N/A"""
    tuner = PromptAutoTuner()

    def evaluate(prompt: str) -> float:
        return 0.9 if "improved" in prompt else 0.1

    def generate_variant(_id):
        new_v = PromptVariant("improved")
        for _ in range(2):
            new_v.record_usage(success=True, feedback_score=1.0)
        tuner.prompt_variants[_id].append(new_v)

    with patch.object(
        PromptAutoTuner, "_generate_variants_if_needed", side_effect=generate_variant
    ):
        tuner.exploration_rate = 0.0
        best = iterative_prompt_adjustment("base", evaluate, iterations=2, tuner=tuner)
    assert "improved" in best.template
