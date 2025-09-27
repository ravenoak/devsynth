"""Tests for the GitHubProjectAdapter."""

import json

import pytest
import responses

from devsynth.adapters.github_project import (
    AddCardVariables,
    AddColumnVariables,
    GitHubProjectAdapter,
    GitHubProjectError,
    ProjectBoard,
    ProjectCard,
    ProjectColumn,
)


def _decode_request_body(body: bytes | str | None) -> str:
    if isinstance(body, bytes):
        return body.decode()
    if isinstance(body, str):
        return body
    raise AssertionError("Request body was empty")


@pytest.mark.fast
def test_payload_serialization() -> None:
    """Variable builders serialize GraphQL payloads explicitly."""

    column_variables = AddColumnVariables(project_id="proj1", name="Todo")
    card_variables = AddCardVariables(column_id="col1", note="Task")

    assert column_variables.to_mapping() == {"projectId": "proj1", "name": "Todo"}
    assert card_variables.to_mapping() == {"columnId": "col1", "note": "Task"}


@pytest.mark.fast
def test_sync_board_creates_columns_and_cards() -> None:
    """Missing columns and cards are created via GraphQL mutations."""

    adapter = GitHubProjectAdapter("token", "org", 1)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={
                "data": {
                    "organization": {
                        "project": {"id": "proj1", "columns": {"nodes": []}}
                    }
                }
            },
            status=200,
        )
        mock.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={
                "data": {"addProjectColumn": {"column": {"id": "col1", "name": "Todo"}}}
            },
            status=200,
        )
        mock.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={
                "data": {
                    "addProjectCard": {
                        "cardEdge": {"node": {"id": "card1", "note": "Task"}}
                    }
                }
            },
            status=200,
        )

        board = ProjectBoard(
            id="local",
            columns=[ProjectColumn(name="Todo", cards=[ProjectCard(note="Task")])],
        )
        adapter.sync_board(board)

        assert len(mock.calls) == 3
        body_query = json.loads(_decode_request_body(mock.calls[1].request.body))
        assert "addProjectColumn" in body_query["query"]
        body_card = json.loads(_decode_request_body(mock.calls[2].request.body))
        assert "addProjectCard" in body_card["query"]


@pytest.mark.fast
def test_sync_board_skips_existing_items() -> None:
    """No mutations are issued when columns and cards already exist."""

    adapter = GitHubProjectAdapter("token", "org", 1)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(
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

        board = ProjectBoard(
            id="local",
            columns=[ProjectColumn(name="Todo", cards=[ProjectCard(note="Task")])],
        )
        adapter.sync_board(board)

        assert len(mock.calls) == 1


@pytest.mark.fast
def test_sync_board_raises_on_graphql_errors() -> None:
    """GraphQL errors are surfaced with a dedicated exception."""

    adapter = GitHubProjectAdapter("token", "org", 1)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"errors": [{"message": "bad request"}]},
            status=200,
        )

        board = ProjectBoard(id="local", columns=[])

        with pytest.raises(GitHubProjectError) as excinfo:
            adapter.sync_board(board)

        assert "bad request" in str(excinfo.value)
