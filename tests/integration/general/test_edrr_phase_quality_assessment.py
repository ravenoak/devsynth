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


class SimpleAgent:
    def __init__(self, name):
        self.name = name
        self.expertise = []
        self.current_role = None

    def process(self, task):
        return {"processed_by": self.name}


@pytest.fixture
def coordinator():
    team = WSDETeam(name="TestEdrrQualityTeam")
    team.add_agent(SimpleAgent("agent1"))
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
    mm.retrieve_with_edrr_phase.side_effect = lambda *a, **k: {}
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=False,
    )


@pytest.mark.slow
def test_phase_quality_markers_are_recorded(coordinator):
    """Each phase records quality metrics and completion status.

    ReqID: N/A"""
    coordinator.start_cycle({"description": "macro"})
    for phase in Phase:
        phase_data = coordinator.results[phase.name]
        assert isinstance(phase_data.get("phase_complete"), bool)
        quality = phase_data.get("quality_score", -1.0)
        assert 0.0 <= quality <= 1.0
