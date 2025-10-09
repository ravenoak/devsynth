import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.edrr.edrr_phase_transitions import MetricType
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "edrr_recursive_recovery.feature"))


class SimpleAgent:
    def __init__(self, name):
        self.name = name
        self.expertise = []
        self.current_role = None

    def process(self, task):
        return {"processed_by": self.name}


@pytest.fixture
def context():
    class Ctx:
        pass

    return Ctx()


@given("an enhanced coordinator with a micro cycle and failing metrics")
def enhanced_coordinator_with_micro_cycle(context):
    mm = MemoryManager(adapters={})
    team = WSDETeam(name="BDDRecoveryTeam")
    team.add_agent(SimpleAgent("agent1"))
    coord = EnhancedEDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(
            mm, storage_path="tests/fixtures/docs"
        ),
    )
    coord.start_cycle({"description": "macro"})
    micro = coord.create_micro_cycle({"description": "micro"}, Phase.EXPAND)
    metrics = {
        MetricType.QUALITY.value: 0.2,
        MetricType.COMPLETENESS.value: 1.0,
        MetricType.CONSISTENCY.value: 1.0,
        MetricType.CONFLICTS.value: 0,
    }
    micro.phase_metrics.end_phase(Phase.EXPAND, metrics)

    def hook(m):
        m[MetricType.QUALITY.value] = 1.0
        return {"recovered": True}

    micro.register_phase_recovery_hook(Phase.EXPAND, hook)
    context.micro = micro


@when("recovery hooks adjust metrics")
def recovery_hooks_adjust_metrics(context):
    context.micro._enhanced_maybe_auto_progress()


@then("the micro cycle transitions to the next phase")
def micro_cycle_transitions(context):
    assert context.micro.current_phase == Phase.DIFFERENTIATE
