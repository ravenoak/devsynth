"""Pure behaviour tests for ``PromiseAgent.create_promise``."""

from __future__ import annotations

import pytest

from devsynth.application.promises import PromiseAgent
from devsynth.application.promises.implementation import Promise

pytestmark = pytest.mark.fast


def test_create_promise_sets_metadata_and_parent_relationship() -> None:
    """Metadata fields and parent-child links are populated deterministically.

    ReqID: N/A
    """

    agent = PromiseAgent(agent_id="agent")
    parent = Promise()
    agent.mixin._pending_requests[parent.id] = parent

    promise = agent.create_promise(
        type="analysis",
        parameters={"task": "review"},
        context_id="ctx-1",
        tags=["quality"],
        parent_id=parent.id,
        priority=3,
    )

    assert isinstance(promise, Promise)
    assert promise.parent_id == parent.id
    assert parent.children_ids == [promise.id]

    assert promise.get_metadata("type") == "analysis"
    assert promise.get_metadata("parameters") == {"task": "review"}
    assert promise.get_metadata("owner_id") == "agent"
    assert promise.get_metadata("context_id") == "ctx-1"
    assert promise.get_metadata("tags") == ["quality"]
    assert promise.get_metadata("priority") == 3
    assert promise.get_metadata("parent_id") == parent.id
