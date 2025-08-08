from unittest.mock import MagicMock

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam

# These tests previously required the ``DEVSYNTH_RUN_WSDE_TESTS`` environment
# variable to be set.  They now execute unconditionally as the global test
# isolation fixture ensures no side effects.


def test_assign_roles_with_explicit_mapping_succeeds():
    """Test that assign roles with explicit mapping succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdeRoleMappingTeam")
    a1 = MagicMock()
    a2 = MagicMock()
    a3 = MagicMock()
    team.add_agents([a1, a2, a3])
    # The primus agent should not also be listed as a worker or the
    # assignment logic will overwrite the Primus role.  Provide a distinct
    # worker mapping to verify role assignment order.
    mapping = {
        "primus": a1,
        "worker": [a2],
        "supervisor": a2,
        "designer": a3,
        "evaluator": None,
    }
    team.assign_roles(mapping)
    assert team.role_assignments["primus"] == a1
    assert a1.current_role == "Primus"
    assert a2.current_role == "Supervisor"
    assert a3.current_role == "Designer"
