import json
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
setattr(rdflib_mod, "Namespace", object)
setattr(rdflib_mod, "RDF", object)
setattr(rdflib_mod, "RDFS", object)
setattr(rdflib_mod, "XSD", object)
namespace_mod = types.ModuleType("namespace")
setattr(namespace_mod, "FOAF", object)
setattr(namespace_mod, "DC", object)
rdflib_mod.namespace = namespace_mod
sys.modules.setdefault("rdflib", rdflib_mod)
sys.modules.setdefault("rdflib.namespace", namespace_mod)
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
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
        return {}


@pytest.fixture
def coordinator(tmp_path):
    manifest = {
        "id": "m1",
        "description": "test",
        "phases": {
            "expand": {"instructions": "e"},
            "differentiate": {"instructions": "d"},
            "refine": {"instructions": "r"},
            "retrospect": {"instructions": "t"},
        },
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    team = WSDETeam(name="TestEdrrManifestDependenciesTeam")
    team.add_agents([SimpleAgent("a1"), SimpleAgent("a2")])
    mm = MagicMock(spec=MemoryManager)
    mm.retrieve_with_edrr_phase.side_effect = lambda *a, **k: {}
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    coord = EDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=False,
    )
    coord.start_cycle_from_manifest(str(path))
    return coord


@pytest.mark.slow
def test_manifest_dependencies_enforced_succeeds(coordinator):
    """Test that manifest dependencies enforced succeeds.

    ReqID: N/A"""
    with pytest.raises(EDRRCoordinatorError):
        coordinator.progress_to_phase(Phase.REFINE)
    coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    coordinator.progress_to_phase(Phase.REFINE)
