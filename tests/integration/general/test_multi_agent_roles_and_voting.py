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
sys.modules.setdefault("chromadb", types.ModuleType("chromadb"))
sys.modules.setdefault("duckdb", types.ModuleType("duckdb"))
sys.modules.setdefault("lmdb", types.ModuleType("lmdb"))
sys.modules.setdefault("faiss", types.ModuleType("faiss"))
from devsynth.adapters.agents.agent_adapter import AgentAdapter
from devsynth.domain.models.wsde_facade import WSDETeam


class SimpleAgent:

    def __init__(self, name, vote=None):
        self.name = name
        self.current_role = None
        self.expertise = []
        self.config = types.SimpleNamespace(name=name, parameters={})
        self._vote = vote

    def process(self, task):
        if self._vote:
            return {"vote": self._vote}
        return {"result": self.name}


@pytest.mark.slow
def test_role_rotation_succeeds():
    """Test that role rotation succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestMultiAgentRolesAndVotingTeam")
    agents = [SimpleAgent(f"a{i}") for i in range(3)]
    team.add_agents(agents)
    team.assign_roles()
    first_primus = team.get_primus().name
    team.rotate_roles()
    second_primus = team.get_primus().name
    assert first_primus != second_primus


@pytest.mark.slow
def test_consensus_vote_with_non_unanimous_votes_succeeds():
    """Test that consensus vote with non unanimous votes succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestMultiAgentRolesAndVotingTeam")
    team.add_agents(
        [SimpleAgent("a1", "x"), SimpleAgent("a2", "y"), SimpleAgent("a3", "y")]
    )
    decision = {
        "type": "critical_decision",
        "is_critical": True,
        "options": [{"id": "x"}, {"id": "y"}],
    }
    result = team.consensus_vote(decision)
    assert result["voting_initiated"]
    assert "winner" in result["result"]
    assert "consensus" in result["result"]


@pytest.mark.slow
def test_agent_adapter_multi_agent_workflow_succeeds():
    """Test that agent adapter multi agent workflow succeeds.

    ReqID: N/A"""
    cfg = {"features": {"wsde_collaboration": True}}
    adapter = AgentAdapter(config=cfg)
    adapter.create_team("t")
    adapter.set_current_team("t")
    a1 = SimpleAgent("a1")
    a2 = SimpleAgent("a2")
    adapter.add_agents_to_team([a1, a2])
    team = adapter.get_team("t")
    team.build_consensus = MagicMock(
        return_value={
            "consensus": "done",
            "contributors": ["a1", "a2"],
            "method": "consensus_synthesis",
        }
    )
    result = adapter.process_task({"description": "demo"})
    team.build_consensus.assert_called_once()
    assert result["method"] == "consensus_synthesis"
