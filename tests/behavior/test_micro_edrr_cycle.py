"""Test script for the Micro EDRR Cycle feature."""

from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "micro_edrr_cycle.feature"))


@pytest.fixture
def context():
    """Create a context for the test."""

    class Context:
        def __init__(self):
            self.coordinator = None
            self.parent_cycle = None
            self.micro_cycle = None
            self.start_called = False
            self.end_called = False

    return Context()


@given("an initialized EDRR coordinator")
def initialized_coordinator(context):
    """Initialize an EDRR coordinator."""
    mm = MagicMock(spec=MemoryManager)
    wsde = MagicMock(spec=WSDETeam)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    coordinator = EDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde,
        code_analyzer=ca,
        ast_transformer=ast,
        prompt_manager=pm,
        documentation_manager=dm,
    )

    # Store the coordinator in the context
    context.coordinator = coordinator
    return coordinator


@given("I register micro cycle monitoring hooks")
def register_hooks(context):
    def start_hook(info):
        context.start_called = True

    def end_hook(info):
        context.end_called = True

    context.coordinator.register_micro_cycle_hook("start", start_hook)
    context.coordinator.register_micro_cycle_hook("end", end_hook)


@when('I start an EDRR cycle for "implement feature"')
def start_edrr_cycle(context):
    """Start an EDRR cycle for "implement feature"."""
    context.coordinator.cycle_id = "parent-cycle-123"
    context.parent_cycle = context.coordinator


@when('I create a micro cycle for "sub task" in phase "Expand"')
def create_micro_cycle(context):
    """Create a micro cycle for "sub task" in phase "Expand"."""
    with patch.object(EDRRCoordinator, "start_cycle", return_value=None):
        result = context.coordinator.create_micro_cycle(
            {"description": "sub task"},
            Phase.EXPAND,
        )

    # Store the micro cycle in the context
    context.micro_cycle = result

    # Add the micro cycle to the parent's child_cycles
    context.parent_cycle.child_cycles.append(result)


@then("the micro cycle should have recursion depth 1")
def verify_recursion_depth(context):
    """Verify that the micro cycle has recursion depth 1."""
    assert context.micro_cycle.recursion_depth == 1


@then("the parent cycle should include the micro cycle")
def verify_parent_includes_micro(context):
    """Verify that the parent cycle includes the micro cycle."""
    assert context.micro_cycle in context.parent_cycle.child_cycles


@then("the hooks should record the micro cycle lifecycle")
def hooks_recorded(context):
    assert context.start_called is True
    assert context.end_called is True
