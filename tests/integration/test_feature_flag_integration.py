from unittest.mock import MagicMock

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.application.collaboration.exceptions import TeamConfigurationError
from devsynth.domain.interfaces.agent import Agent
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:
    def __init__(self, name, expertise, agent_type=None):
        self.name = name
        self.expertise = expertise
        self.agent_type = agent_type or name
        self.current_role = None

    def get_capabilities(self):
        return self.expertise

    def initialize(self, config=None):
        pass

    def process(self, task):
        return {"solution": f"{self.name}-result"}

    def set_llm_port(self, llm_port):
        pass


def create_edrr_coordinator(auto_enabled: bool) -> EDRRCoordinator:
    team = WSDETeam()
    team.add_agents(
        [
            SimpleAgent("expand", ["expand"]),
            SimpleAgent("diff", ["differentiate"]),
            SimpleAgent("refine", ["refine"]),
            SimpleAgent("retro", ["retrospect"]),
        ]
    )
    team.generate_diverse_ideas = MagicMock(return_value=["idea"])
    team.create_comparison_matrix = MagicMock(return_value={})
    team.evaluate_options = MagicMock(return_value=[])
    team.analyze_trade_offs = MagicMock(return_value=[])
    team.formulate_decision_criteria = MagicMock(return_value={})
    team.select_best_option = MagicMock(return_value={})
    team.elaborate_details = MagicMock(return_value=[])
    team.create_implementation_plan = MagicMock(return_value=[])
    team.optimize_implementation = MagicMock(return_value={})
    team.perform_quality_assurance = MagicMock(return_value={})
    team.extract_learnings = MagicMock(return_value=[])
    team.recognize_patterns = MagicMock(return_value=[])
    team.integrate_knowledge = MagicMock(return_value={})
    team.generate_improvement_suggestions = MagicMock(return_value=[])

    mm = MagicMock(spec=MemoryManager)

    def retrieve_with_phase(item_type, phase, metadata):
        if item_type == "EXPAND_RESULTS":
            return {"ideas": []}
        if item_type == "DIFFERENTIATE_RESULTS":
            return {"evaluated_options": [], "decision_criteria": {}}
        if item_type == "REFINE_RESULTS":
            return {"implementation_plan": [], "quality_checks": {}}
        return {}

    mm.retrieve_with_edrr_phase.side_effect = retrieve_with_phase
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []

    config = {
        "edrr": {"phase_transition": {"auto": auto_enabled, "timeout": 0}},
        "features": {"automatic_phase_transitions": auto_enabled},
    }

    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=False,
        config=config,
    )


def create_agent_coordinator(collab_enabled: bool) -> AgentCoordinatorImpl:
    return AgentCoordinatorImpl({"features": {"wsde_collaboration": collab_enabled}})


def add_basic_agents(coordinator: AgentCoordinatorImpl) -> None:
    agents = []
    for name, agent_type in [
        ("planner", "planner"),
        ("coder", "code"),
        ("tester", "test"),
        ("validator", "validation"),
    ]:
        agent = MagicMock(spec=Agent)
        agent.name = name
        agent.agent_type = agent_type
        agent.current_role = None
        agent.process.return_value = {"solution": f"{name}-solution"}
        agents.append(agent)
        coordinator.add_agent(agent)


class TestEDRRPhaseTransitions:
    def test_auto_transitions_enabled(self):
        coordinator = create_edrr_coordinator(True)
        task = {"description": "demo"}
        coordinator.start_cycle(task)
        assert coordinator.current_phase == Phase.RETROSPECT
        calls = [
            c.args[2]
            for c in coordinator.memory_manager.store_with_edrr_phase.call_args_list
            if c.args[1] == "ROLE_ASSIGNMENT"
        ]
        calls = calls[-4:]
        assert calls == [
            Phase.EXPAND.value,
            Phase.DIFFERENTIATE.value,
            Phase.REFINE.value,
            Phase.RETROSPECT.value,
        ]

    def test_manual_transitions_when_disabled(self):
        coordinator = create_edrr_coordinator(False)
        task = {"description": "demo"}
        coordinator.start_cycle(task)
        assert coordinator.current_phase == Phase.EXPAND
        coordinator.progress_to_next_phase()
        assert coordinator.current_phase == Phase.DIFFERENTIATE
        coordinator.progress_to_next_phase()
        assert coordinator.current_phase == Phase.REFINE
        coordinator.progress_to_next_phase()
        assert coordinator.current_phase == Phase.RETROSPECT
        with pytest.raises(EDRRCoordinatorError):
            coordinator.progress_to_next_phase()


class TestWSDECollaboration:
    def test_collaboration_enabled(self):
        coordinator = create_agent_coordinator(True)
        add_basic_agents(coordinator)
        task = {"team_task": True, "action": "implement"}
        result = coordinator.delegate_task(task)
        assert "team_result" in result
        assert result["team_result"]["solutions"]
        assert result["result"]

    def test_collaboration_disabled(self):
        coordinator = create_agent_coordinator(False)
        task = {"team_task": True, "action": "implement"}
        result = coordinator.delegate_task(task)
        assert result == {"success": False, "error": "Collaboration disabled"}

    def test_collaboration_no_agents(self):
        coordinator = create_agent_coordinator(True)
        task = {"team_task": True, "action": "implement"}
        with pytest.raises(TeamConfigurationError):
            coordinator.delegate_task(task)

