from unittest.mock import MagicMock

from devsynth.domain.models.wsde import WSDETeam
import pytest

pytest.skip("WSDE role mapping tests skipped", allow_module_level=True)


def test_assign_roles_with_explicit_mapping():
    team = WSDETeam()
    a1 = MagicMock()
    a2 = MagicMock()
    a3 = MagicMock()
    team.add_agents([a1, a2, a3])

    mapping = {
        "primus": a1,
        "worker": [a1],
        "supervisor": a2,
        "designer": a3,
        "evaluator": None,
    }

    team.assign_roles(mapping)

    assert team.role_assignments["primus"] == a1
    assert a1.current_role == "Primus"
    assert a2.current_role == "Supervisor"
    assert a3.current_role == "Designer"

