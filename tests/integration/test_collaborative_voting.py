from unittest.mock import MagicMock
import types
import sys
import pytest
argon2_mod = types.ModuleType('argon2')
setattr(argon2_mod, 'PasswordHasher', object)
exceptions_mod = types.ModuleType('exceptions')
setattr(exceptions_mod, 'VerifyMismatchError', type('VerifyMismatchError',
    (), {}))
setattr(argon2_mod, 'exceptions', exceptions_mod)
sys.modules.setdefault('argon2', argon2_mod)
sys.modules.setdefault('argon2.exceptions', exceptions_mod)
sys.modules.setdefault('requests', types.ModuleType('requests'))
crypto_mod = types.ModuleType('cryptography')
fernet_mod = types.ModuleType('fernet')
setattr(fernet_mod, 'Fernet', object)
crypto_mod.fernet = fernet_mod
sys.modules.setdefault('cryptography', crypto_mod)
sys.modules.setdefault('cryptography.fernet', fernet_mod)
sys.modules.setdefault('jsonschema', types.ModuleType('jsonschema'))
rdflib_mod = types.ModuleType('rdflib')
setattr(rdflib_mod, 'Graph', object)
setattr(rdflib_mod, 'Literal', object)
setattr(rdflib_mod, 'URIRef', object)
setattr(rdflib_mod, 'Namespace', lambda *a, **k: object())
setattr(rdflib_mod, 'RDF', object)
setattr(rdflib_mod, 'RDFS', object)
setattr(rdflib_mod, 'XSD', object)
namespace_mod = types.ModuleType('namespace')
setattr(namespace_mod, 'FOAF', object)
setattr(namespace_mod, 'DC', object)
rdflib_mod.namespace = namespace_mod
sys.modules.setdefault('rdflib', rdflib_mod)
sys.modules.setdefault('rdflib.namespace', namespace_mod)
astor_mod = types.ModuleType('astor')
setattr(astor_mod, 'to_source', lambda *a, **k: '')
sys.modules.setdefault('astor', astor_mod)
from devsynth.application.collaboration.collaborative_wsde_team import CollaborativeWSDETeam


class VotingAgent:

    def __init__(self, name, vote, expertise=None, level='expert'):
        self.name = name
        self.vote = vote
        self.current_role = None
        if expertise is None:
            expertise = ['general']
        self.config = types.SimpleNamespace(name=name, parameters={
            'expertise': expertise, 'expertise_level': level})

    def process(self, task):
        return {'vote': self.vote}


def test_majority_voting_succeeds():
    """Test that majority voting succeeds.

ReqID: N/A"""
    team = CollaborativeWSDETeam(name='TestCollaborativeVotingTeam')
    team.add_agents([VotingAgent('a1', 'o1'), VotingAgent('a2', 'o2'),
        VotingAgent('a3', 'o2')])
    decision = {'type': 'critical_decision', 'is_critical': True, 'options':
        [{'id': 'o1'}, {'id': 'o2'}]}
    result = team.collaborative_decision(decision)
    assert result['result']['winner'] == 'o2'


def test_weighted_voting_succeeds():
    """Test that weighted voting succeeds.

ReqID: N/A"""
    team = CollaborativeWSDETeam(name='TestCollaborativeVotingTeam')
    team.add_agents([VotingAgent('e1', 'o1', expertise=['ml'], level=
        'expert'), VotingAgent('e2', 'o2', expertise=['ml'], level='novice')])
    decision = {'type': 'critical_decision', 'is_critical': True, 'domain':
        'ml', 'options': [{'id': 'o1'}, {'id': 'o2'}]}
    result = team.collaborative_decision(decision)
    assert result['result']['winner'] == 'o1'
