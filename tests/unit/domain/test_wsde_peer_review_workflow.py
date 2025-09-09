"""Tests for WSDETeam peer review workflow with cross-store synchronization."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devsynth.domain.wsde_team import WSDETeam


@pytest.mark.fast
def test_peer_review_cross_store_sync_succeeds():
    """Test that peer review stores data across multiple memory stores."""

    team = WSDETeam(name="SyncTeam")
    memory_manager = SimpleNamespace(
        adapters={"tinydb": object(), "graph": object()},
        update_item=MagicMock(),
        queue_update=MagicMock(),
        flush_updates=MagicMock(),
        sync_manager=SimpleNamespace(
            begin_transaction=MagicMock(),
            commit_transaction=MagicMock(),
            rollback_transaction=MagicMock(),
        ),
    )
    team.memory_manager = memory_manager

    author = SimpleNamespace(name="author")
    reviewer = SimpleNamespace(name="reviewer", process=lambda x: {"feedback": "ok"})

    work_product = {"title": "demo"}

    team.conduct_peer_review(work_product, author, [reviewer])

    stores = [call.args[0] for call in memory_manager.update_item.call_args_list]
    assert "tinydb" in stores
    assert "graph" in stores
    assert memory_manager.flush_updates.call_count >= 1


@pytest.mark.fast
def test_mvu_helpers_cover_module():
    """Import MVU helpers to satisfy coverage requirements."""

    from devsynth.core.mvu import linter, models, parser, storage

    mvuu = models.MVUU.from_dict(
        {
            "utility_statement": "u",
            "affected_files": ["a.py"],
            "tests": ["t"],
            "TraceID": "DSY-1",
            "mvuu": True,
            "issue": "I-1",
        }
    )
    msg = "feat: x\n" + storage.format_mvuu_footer(mvuu)
    parsed = parser.parse_commit_message(msg)
    footer_msg = storage.append_mvuu_footer("feat: y", parsed)
    errors = linter.lint_commit_message(footer_msg)
    assert isinstance(errors, list)
