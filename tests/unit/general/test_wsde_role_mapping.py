from unittest.mock import MagicMock
from devsynth.domain.models.wsde import WSDETeam
import pytest
import os
if os.environ.get('DEVSYNTH_RUN_WSDE_TESTS') != '1':
    pytest.skip('WSDE role mapping tests require DEVSYNTH_RUN_WSDE_TESTS=1', allow_module_level=True)


def test_assign_roles_with_explicit_mapping_succeeds():
    """Test that assign roles with explicit mapping succeeds.

ReqID: N/A"""
    team = WSDETeam(name='TestWsdeRoleMappingTeam')
    a1 = MagicMock()
    a2 = MagicMock()
    a3 = MagicMock()
    team.add_agents([a1, a2, a3])
    mapping = {'primus': a1, 'worker': [a1], 'supervisor': a2, 'designer':
        a3, 'evaluator': None}
    team.assign_roles(mapping)
    assert team.role_assignments['primus'] == a1
    assert a1.current_role == 'Primus'
    assert a2.current_role == 'Supervisor'
    assert a3.current_role == 'Designer'
