from unittest.mock import MagicMock
from devsynth.application.collaboration.WSDE import WSDE


def test_reassign_roles_uses_dynamic_reassignment():
    wsde = WSDE(name="team")
    wsde.dynamic_role_reassignment = MagicMock(return_value={"ok": True})
    task = {"id": "1"}
    result = wsde.reassign_roles(task)
    wsde.dynamic_role_reassignment.assert_called_once_with(task)
    assert result == {"ok": True}


def test_run_consensus_falls_back_to_build():
    wsde = WSDE(name="team")
    wsde.consensus_vote = MagicMock(return_value={"status": "incomplete"})
    wsde.build_consensus = MagicMock(return_value={"decision": "x"})
    task = {"id": "2"}
    result = wsde.run_consensus(task)
    wsde.consensus_vote.assert_called_once_with(task)
    wsde.build_consensus.assert_called_once_with(task)
    assert result["consensus"] == {"decision": "x"}


def test_run_consensus_no_fallback_when_complete():
    wsde = WSDE(name="team")
    wsde.consensus_vote = MagicMock(return_value={"status": "completed", "decision": "y"})
    wsde.build_consensus = MagicMock()
    task = {"id": "3"}
    result = wsde.run_consensus(task)
    wsde.consensus_vote.assert_called_once_with(task)
    wsde.build_consensus.assert_not_called()
    assert result == {"status": "completed", "decision": "y"}
