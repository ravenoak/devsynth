import sys
import types
from unittest.mock import MagicMock

import pytest

argon2_mod = types.ModuleType("argon2")
setattr(argon2_mod, "PasswordHasher", object)
exceptions_mod = types.ModuleType("exceptions")
setattr(exceptions_mod, "VerifyMismatchError", type("VerifyMismatchError", (), {}))
setattr(argon2_mod, "exceptions", exceptions_mod)
sys.modules.setdefault("argon2", argon2_mod)
sys.modules.setdefault("argon2.exceptions", exceptions_mod)
sys.modules.setdefault("requests", types.ModuleType("requests"))
crypto_mod = types.ModuleType("cryptography")
fernet_mod = types.ModuleType("fernet")
setattr(fernet_mod, "Fernet", object)
crypto_mod.fernet = fernet_mod
sys.modules.setdefault("cryptography", crypto_mod)
sys.modules.setdefault("cryptography.fernet", fernet_mod)
sys.modules.setdefault("jsonschema", types.ModuleType("jsonschema"))
rdflib_mod = types.ModuleType("rdflib")
setattr(rdflib_mod, "Graph", object)
setattr(rdflib_mod, "Literal", object)
setattr(rdflib_mod, "URIRef", object)
setattr(rdflib_mod, "Namespace", lambda *a, **k: object())
setattr(rdflib_mod, "RDF", object)
setattr(rdflib_mod, "RDFS", object)
setattr(rdflib_mod, "XSD", object)
namespace_mod = types.ModuleType("namespace")
setattr(namespace_mod, "FOAF", object)
setattr(namespace_mod, "DC", object)
rdflib_mod.namespace = namespace_mod
sys.modules.setdefault("rdflib", rdflib_mod)
sys.modules.setdefault("rdflib.namespace", namespace_mod)
astor_mod = types.ModuleType("astor")
setattr(astor_mod, "to_source", lambda *a, **k: "")
sys.modules.setdefault("astor", astor_mod)
tinydb_mod = types.ModuleType("tinydb")
setattr(tinydb_mod, "TinyDB", object)
setattr(tinydb_mod, "Query", object)
storages_mod = types.ModuleType("storages")
setattr(storages_mod, "MemoryStorage", object)
setattr(storages_mod, "JSONStorage", object)
tinydb_mod.storages = storages_mod
sys.modules.setdefault("tinydb", tinydb_mod)
sys.modules.setdefault("tinydb.storages", storages_mod)
middlewares_mod = types.ModuleType("middlewares")
setattr(middlewares_mod, "CachingMiddleware", object)
tinydb_mod.middlewares = middlewares_mod
sys.modules.setdefault("tinydb.middlewares", middlewares_mod)
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:

    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.current_role = None


@pytest.fixture
def coordinator():
    team = WSDETeam(name="TestEdrrAutoPhaseTransitionTeam")
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
        if item_type == MemoryType.EXPAND_RESULTS:
            return {"ideas": []}
        if item_type == MemoryType.DIFFERENTIATE_RESULTS:
            return {"evaluated_options": [], "decision_criteria": {}}
        if item_type == MemoryType.REFINE_RESULTS:
            return {"implementation_plan": [], "quality_checks": {}}
        return {}

    mm.retrieve_with_edrr_phase.side_effect = retrieve_with_phase
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    config = {
        "edrr": {"phase_transition": {"auto": True, "timeout": 0}},
        "features": {"automatic_phase_transitions": True},
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


@pytest.mark.slow
def test_full_cycle_auto_transition_dynamic_roles_succeeds(coordinator):
    """Test that full cycle auto transition dynamic roles succeeds.

    ReqID: N/A"""
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


@pytest.mark.slow
def test_micro_cycle_results_aggregated_succeeds(coordinator):
    """Ensure micro cycles spawn and results are aggregated.

    ReqID: N/A"""
    valid_task = {"description": "child valid", "granularity_score": 0.8}
    terminate_task = {"description": "child stop", "granularity_score": 0.1}
    original_expand = coordinator._execute_expand_phase

    def expand_with_micro(context=None):
        context = {"micro_tasks": [valid_task, terminate_task]}
        return original_expand(context)

    coordinator._execute_expand_phase = expand_with_micro
    coordinator.start_cycle({"description": "macro"})
    assert coordinator.current_phase == Phase.RETROSPECT
    assert len(coordinator.child_cycles) == 1
    child = coordinator.child_cycles[0]
    expand_results = coordinator.results[Phase.EXPAND.name]
    assert child.cycle_id in expand_results["micro_cycle_results"]
    assert "child stop" in expand_results["micro_cycle_results"]
    assert "error" in expand_results["micro_cycle_results"]["child stop"]
    aggregated = coordinator.results["AGGREGATED"]
    assert child.cycle_id in aggregated["child_cycles"]
    assert aggregated["child_cycles"][child.cycle_id] == child.results
    assert any(
        call.args[1] == "MICRO_CYCLE"
        for call in coordinator.memory_manager.store_with_edrr_phase.call_args_list
    )
    assert coordinator.should_terminate_recursion(terminate_task) is True
    assert coordinator.should_terminate_recursion(valid_task) is False
