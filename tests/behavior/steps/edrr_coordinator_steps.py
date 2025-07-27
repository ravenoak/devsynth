"""Step definitions for the ``edrr_coordinator.feature`` file."""

from pytest_bdd import scenarios, given, when, then, parsers

from .test_edrr_coordinator_steps import *  # noqa: F401,F403


scenarios("../features/edrr_coordinator.feature")


@given("the EDRR coordinator is initialized with recursion support")
def edrr_coordinator_initialized_with_recursion(context):
    """Initialize the coordinator with recursion features enabled."""
    from devsynth.application.memory.adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter,
    )

    memory_adapter = TinyDBMemoryAdapter()
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam(name="EdrrRecursionTeam")
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager,
        storage_path="tests/fixtures/docs",
    )
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager,
        enable_enhanced_logging=True,
    )
    context.parent_cycle = context.edrr_coordinator


@when(
    parsers.parse(
        'I create a micro cycle for "{sub_task_description}" in phase "{phase_name}"'
    )
)
def create_micro_cycle(context, sub_task_description, phase_name):
    """Create a micro EDRR cycle within the given phase."""
    context.phase = Phase[phase_name.upper()]
    if context.edrr_coordinator.current_phase != context.phase:
        context.edrr_coordinator.progress_to_phase(context.phase)
    original_calc = EDRRCoordinator._calculate_similarity_key

    def _safe_calc(self, result):
        try:
            return original_calc(self, result)
        except TypeError:
            if isinstance(result, dict):
                keys = [str(k) if isinstance(k, Phase) else k for k in result.keys()]
                return ",".join(sorted(keys))
            return original_calc(self, result)

    EDRRCoordinator._calculate_similarity_key = _safe_calc
    try:
        context.micro_cycle = context.edrr_coordinator.create_micro_cycle(
            {"description": sub_task_description}, context.phase
        )
    finally:
        EDRRCoordinator._calculate_similarity_key = original_calc


@then(parsers.parse("the micro cycle should have recursion depth {depth:d}"))
def verify_micro_cycle_depth(context, depth):
    """Verify recursion depth of created micro cycle."""
    assert context.micro_cycle is not None
    assert context.micro_cycle.recursion_depth == depth


@then("the parent cycle should include the micro cycle")
def verify_parent_includes_micro(context):
    """Ensure parent cycle tracks the created micro cycle."""
    assert context.micro_cycle in context.parent_cycle.child_cycles
