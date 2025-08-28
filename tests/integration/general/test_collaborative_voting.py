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
from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager


class VotingAgent:

    def __init__(self, name, vote, expertise=None, level="expert"):
        self.name = name
        self.vote = vote
        self.current_role = None
        if expertise is None:
            expertise = ["general"]
        self.config = types.SimpleNamespace(
            name=name, parameters={"expertise": expertise, "expertise_level": level}
        )
        self.expertise = expertise
        self.metadata = {"expertise": expertise}

    def process(self, task):
        return {"vote": self.vote}


@pytest.mark.medium
def test_majority_voting_succeeds():
    """Test that majority voting succeeds.

    ReqID: N/A"""
    team = CollaborativeWSDETeam(name="TestCollaborativeVotingTeam")
    team.add_agents(
        [VotingAgent("a1", "o1"), VotingAgent("a2", "o2"), VotingAgent("a3", "o2")]
    )
    decision = {
        "type": "critical_decision",
        "is_critical": True,
        "options": ["o1", "o2"],
    }
    result = team.collaborative_decision(decision)
    assert result["result"] in {"o1", "o2"}


@pytest.mark.medium
def test_weighted_voting_succeeds():
    """Test that weighted voting succeeds.

    ReqID: N/A"""
    team = CollaborativeWSDETeam(name="TestCollaborativeVotingTeam")
    team.add_agents(
        [
            VotingAgent("e1", "o1", expertise=["ml"], level="expert"),
            VotingAgent("e2", "o2", expertise=["ml"], level="novice"),
        ]
    )
    decision = {
        "type": "critical_decision",
        "is_critical": True,
        "domain": "ml",
        "options": ["o1", "o2"],
    }
    result = team.collaborative_decision(decision)
    assert result["result"] in {"o1", "o2"}


@pytest.mark.medium
def test_voting_result_syncs_to_memory():
    """Voting results should be stored across memory stores."""
    adapters = {
        "tinydb": TinyDBMemoryAdapter(),
        "secondary": TinyDBMemoryAdapter(),
    }
    manager = MemoryManager(adapters=adapters)
    team = CollaborativeWSDETeam(name="TestTeam", memory_manager=manager)
    team.add_agents([VotingAgent("a1", "o1"), VotingAgent("a2", "o2")])
    decision = {
        "id": "vote1",
        "type": "critical_decision",
        "is_critical": True,
        "options": ["o1", "o2"],
    }
    team.collaborative_decision(decision)
    team.build_consensus(decision)
    decision_id = next(iter(team.tracked_decisions))
    for name, adapter in adapters.items():
        stored = adapter.search({"id": decision_id})
        assert stored, f"decision not stored in {name}"
