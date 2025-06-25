from pytest_bdd import given, when, then, scenarios, parsers
import pytest

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase

scenarios("../features/micro_edrr_cycle.feature")


@pytest.fixture
def context(tmp_path):
    class Context:
        pass

    ctx = Context()
    ctx.base = tmp_path
    return ctx


@given("an initialized EDRR coordinator")
def init_coordinator(context):
    memory_adapter = TinyDBMemoryAdapter()
    memory_manager = MemoryManager({"tinydb": memory_adapter})
    wsde_team = WSDETeam()
    code_analyzer = CodeAnalyzer()
    ast_transformer = AstTransformer()
    prompt_manager = PromptManager(storage_path=str(context.base / "prompts"))
    documentation_manager = DocumentationManager(
        memory_manager, storage_path=str(context.base / "docs")
    )
    context.coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
    )


@when(parsers.parse('I start an EDRR cycle for "{task}"'))
def start_cycle(context, task):
    context.coordinator.start_cycle({"description": task})


@when(parsers.parse('I create a micro cycle for "{subtask}" in phase "{phase}"'))
def create_micro(context, subtask, phase):
    micro = context.coordinator.create_micro_cycle(
        {"description": subtask}, Phase[phase.upper()]
    )
    context.micro = micro


@then("the micro cycle should have recursion depth 1")
def check_depth(context):
    assert context.micro.recursion_depth == 1


@then("the parent cycle should include the micro cycle")
def parent_has_child(context):
    assert context.micro in context.coordinator.child_cycles
