from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType


def make_agent(monkeypatch):
    agent = UnifiedAgent()
    cfg = AgentConfig(name='ua', agent_type=AgentType.ORCHESTRATOR,
        description='', capabilities=[])
    agent.initialize(cfg)
    monkeypatch.setattr(agent, 'generate_text', lambda p: p)
    return agent


def test_process_code_task_includes_language_and_paradigm_succeeds(monkeypatch
    ):
    """Test that process code task includes language and paradigm succeeds.

ReqID: N/A"""
    agent = make_agent(monkeypatch)
    result = agent.process({'task_type': 'code', 'language': 'python',
        'paradigm': 'functional'})
    assert 'functional' in result['code']
    assert 'python' in result['code']
