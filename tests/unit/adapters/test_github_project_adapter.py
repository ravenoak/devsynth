"""Tests for the GitHubProjectAdapter."""

import json

import pytest
import responses

from devsynth.adapters.github_project import GitHubProjectAdapter


@pytest.mark.fast
@responses.activate
def test_sync_board_creates_columns_and_cards() -> None:
    """Missing columns and cards are created via GraphQL mutations."""
    adapter = GitHubProjectAdapter("token", "org", 1)

    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={
            "data": {
                "organization": {"project": {"id": "proj1", "columns": {"nodes": []}}}
            }
        },
        status=200,
    )
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={"data": {"addProjectColumn": {"column": {"id": "col1"}}}},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={"data": {"addProjectCard": {"cardEdge": {"node": {"id": "card1"}}}}},
        status=200,
    )

    board = {"columns": [{"name": "Todo", "cards": [{"note": "Task"}]}]}
    adapter.sync_board(board)

    assert len(responses.calls) == 3
    body_query = json.loads(responses.calls[1].request.body)
    assert "addProjectColumn" in body_query["query"]
    body_card = json.loads(responses.calls[2].request.body)
    assert "addProjectCard" in body_card["query"]


@responses.activate
def test_sync_board_skips_existing_items() -> None:
    """No mutations are issued when columns and cards already exist."""
    adapter = GitHubProjectAdapter("token", "org", 1)

    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={
            "data": {
                "organization": {
                    "project": {
                        "id": "proj1",
                        "columns": {
                            "nodes": [
                                {
                                    "id": "col1",
                                    "name": "Todo",
                                    "cards": {
                                        "nodes": [{"id": "card1", "note": "Task"}]
                                    },
                                }
                            ]
                        },
                    }
                }
            }
        },
        status=200,
    )

    board = {"columns": [{"name": "Todo", "cards": [{"note": "Task"}]}]}
    adapter.sync_board(board)

    assert len(responses.calls) == 1
