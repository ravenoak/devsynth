"""
Advanced integration tests for WSDE-EDRR integration.

This test file focuses on advanced aspects of the integration between the WSDE agent model
and the EDRR framework, including phase-specific role assignment, quality-based phase transitions,
micro-cycle implementation, error handling, and performance metrics.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.methodology.base import Phase
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.application.agents.unified_agent import UnifiedAgent


class ExpertAgent(UnifiedAgent):
    """Agent with specific expertise for testing."""

    def __init__(self, name, expertise):
        super().__init__()
        self.expertise = expertise
        self.current_role = None
        self.previous_role = None
        self.has_been_primus = False
        self.process_calls = []
        config = AgentConfig(name=name, agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with expertise in {', '.join(expertise)}",
            capabilities=[], parameters={'expertise': expertise})
        self.initialize(config)

    def process(self, task):
        """Process a task based on agent's expertise."""
        self.process_calls.append(task)
        return {'result': f'Solution from {self.name}', 'confidence': 0.9,
            'reasoning':
            f"Based on my expertise in {', '.join(self.expertise)}"}


@pytest.fixture
def enhanced_coordinator():
    """Create an EnhancedEDRRCoordinator with a team of agents with different expertise."""
    team = WSDETeam(name='TestWsdeEdrrIntegrationAdvancedTeam')
    expand_agent = ExpertAgent('expand_agent', ['brainstorming',
        'exploration', 'creativity', 'ideation'])
    diff_agent = ExpertAgent('diff_agent', ['comparison', 'analysis',
        'evaluation', 'critical thinking'])
    refine_agent = ExpertAgent('refine_agent', ['implementation', 'coding',
        'development', 'optimization'])
    retro_agent = ExpertAgent('retro_agent', ['evaluation', 'reflection',
        'learning', 'improvement'])
    team.add_agents([expand_agent, diff_agent, refine_agent, retro_agent])
    mm = MagicMock(spec=MemoryManager)
    mm.retrieve_with_edrr_phase.return_value = {}
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    mm.store_with_edrr_phase.return_value = 'memory_id'
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    coordinator = EnhancedEDRRCoordinator(memory_manager=mm, wsde_team=team,
        code_analyzer=analyzer, ast_transformer=MagicMock(spec=
        AstTransformer), prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager), config=
        {'edrr': {'quality_based_transitions': True, 'phase_transition': {
        'auto': True}, 'micro_cycles': {'enabled': True, 'max_iterations': 3}}}
        )
    coordinator.agents = {'expand_agent': expand_agent, 'diff_agent':
        diff_agent, 'refine_agent': refine_agent, 'retro_agent': retro_agent}
    return coordinator


def test_phase_specific_role_assignment_has_expected(enhanced_coordinator):
    """Test that roles are assigned based on the current EDRR phase.

ReqID: N/A"""
    task = {'description':
        'Create a Python function to calculate Fibonacci numbers',
        'language': 'python', 'domain': 'code_generation'}
    enhanced_coordinator.start_cycle(task)
    expand_primus = enhanced_coordinator.wsde_team.get_primus()
    assert expand_primus is not None
    assert any(skill in ['analysis', 'evaluation', 'brainstorming'] for
        skill in expand_primus.expertise)
    enhanced_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    diff_primus = enhanced_coordinator.wsde_team.get_primus()
    assert diff_primus is not None
    assert any(skill in ['comparison', 'analysis', 'evaluation'] for skill in
        diff_primus.expertise)
    enhanced_coordinator.progress_to_phase(Phase.REFINE)
    refine_primus = enhanced_coordinator.wsde_team.get_primus()
    assert refine_primus is not None
    assert any(skill in ['brainstorming', 'exploration', 'creativity', 'ideation'] for
        skill in refine_primus.expertise)
    enhanced_coordinator.progress_to_phase(Phase.RETROSPECT)
    retro_primus = enhanced_coordinator.wsde_team.get_primus()
    assert retro_primus is not None
    assert any(skill in ['evaluation', 'reflection', 'learning'] for skill in
        retro_primus.expertise)


def test_quality_based_phase_transitions_has_expected(enhanced_coordinator):
    """Test that phase transitions are based on quality metrics from the WSDE team.

ReqID: N/A"""
    task = {'description':
        'Create a Python function to calculate Fibonacci numbers',
        'language': 'python', 'domain': 'code_generation'}
    enhanced_coordinator.start_cycle(task)
    with patch.object(enhanced_coordinator, '_assess_phase_quality',
        return_value={'quality': 0.9, 'can_progress': True}):
        enhanced_coordinator._enhanced_maybe_auto_progress()
        assert enhanced_coordinator.current_phase == Phase.DIFFERENTIATE
    with patch.object(enhanced_coordinator, '_assess_phase_quality',
        return_value={'quality': 0.3, 'can_progress': False}):
        enhanced_coordinator._enhanced_maybe_auto_progress()
        assert enhanced_coordinator.current_phase == Phase.DIFFERENTIATE


def test_micro_cycle_implementation_succeeds(enhanced_coordinator):
    """Test the micro-cycle implementation with the WSDE team.

ReqID: N/A"""
    task = {'description':
        'Create a Python function to calculate Fibonacci numbers',
        'language': 'python', 'domain': 'code_generation'}
    enhanced_coordinator.start_cycle(task)
    original_execute_micro_cycle = enhanced_coordinator._execute_micro_cycle
    micro_cycle_calls = []

    def mock_execute_micro_cycle(phase, iteration):
        micro_cycle_calls.append((phase, iteration))
        return {'result':
            f'Micro-cycle result for {phase.name}, iteration {iteration}'}
    enhanced_coordinator._execute_micro_cycle = mock_execute_micro_cycle
    enhanced_coordinator.execute_current_phase()
    assert len(micro_cycle_calls) > 0
    enhanced_coordinator._execute_micro_cycle = original_execute_micro_cycle


def test_error_handling_and_recovery_raises_error(enhanced_coordinator):
    """Test error handling and recovery in WSDE-EDRR integration.

ReqID: N/A"""
    task = {'description':
        'Create a Python function to calculate Fibonacci numbers',
        'language': 'python', 'domain': 'code_generation'}
    enhanced_coordinator.start_cycle(task)
    original_process = enhanced_coordinator.wsde_team.process
    enhanced_coordinator.wsde_team.process = MagicMock(side_effect=
        Exception('Test exception'))
    try:
        results = enhanced_coordinator.execute_current_phase()
        assert 'error' in results
        assert 'Test exception' in str(results['error'])
    except Exception:
        assert False, 'Exception was not handled properly'
    enhanced_coordinator.wsde_team.process = original_process


def test_performance_metrics_and_traceability_succeeds(enhanced_coordinator):
    """Test performance metrics and traceability in WSDE-EDRR integration.

ReqID: N/A"""
    task = {'description':
        'Create a Python function to calculate Fibonacci numbers',
        'language': 'python', 'domain': 'code_generation'}
    enhanced_coordinator.start_cycle(task)
    enhanced_coordinator.execute_current_phase()
    traces = enhanced_coordinator.get_execution_traces()
    assert traces is not None
    assert 'phases' in traces
    assert Phase.EXPAND.name in traces['phases']
    assert 'metrics' in traces['phases'][Phase.EXPAND.name]
    assert 'wsde_team' in traces['phases'][Phase.EXPAND.name]['metrics'][
        'component_calls']
    metrics = enhanced_coordinator.get_performance_metrics()
    assert metrics is not None
    assert Phase.EXPAND.name in metrics
    assert 'component_calls' in metrics[Phase.EXPAND.name]
    assert 'wsde_team' in metrics[Phase.EXPAND.name]['component_calls']
