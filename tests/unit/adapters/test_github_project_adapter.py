"""Tests for the GitHubProjectAdapter."""

import json
from dataclasses import dataclass
from collections.abc import Iterator, Mapping

import pytest
import responses

from devsynth.adapters.github_project import (
    AddCardVariables,
    AddColumnVariables,
    GitHubProjectAdapter,
    GitHubProjectError,
    GraphQLHTTPClient,
    GraphQLHTTPResponse,
    GraphQLRequest,
    ProjectBoard,
    ProjectCard,
    ProjectColumn,
)


@dataclass
class StubResponse(GraphQLHTTPResponse):
    """Minimal in-memory response object for exercising GraphQL flows."""

    payload: Mapping[str, object]

    def raise_for_status(self) -> None:  # pragma: no cover - nothing to raise in stub
        return None

    def json(self) -> object:
        return dict(self.payload)


class StubHTTPClient(GraphQLHTTPClient):
    """Collects GraphQL requests and yields predefined responses."""

    def __init__(self, responses_iter: Iterator[GraphQLHTTPResponse]):
        self._responses = responses_iter
        self.captured: list[GraphQLRequest] = []

    def post(
        self,
        url: str,
        *,
        json: Mapping[str, object],
        headers: Mapping[str, str],
        timeout: int,
    ) -> GraphQLHTTPResponse:
        query_raw = json["query"]
        variables_raw = json["variables"]
        if not isinstance(query_raw, str) or not isinstance(variables_raw, Mapping):
            raise AssertionError("StubHTTPClient received invalid request payload")
        self.captured.append(GraphQLRequest(query=query_raw, variables=variables_raw))
        try:
            return next(self._responses)
        except StopIteration as exc:  # pragma: no cover - defensive guard in tests
            raise AssertionError("StubHTTPClient ran out of responses") from exc


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
def test_graphql_request_payload_and_helpers() -> None:
    """Utility dataclasses expose deterministic helper methods."""

    request = GraphQLRequest(query="query Test { noop }", variables={"a": 1})
    assert request.payload() == {"query": "query Test { noop }", "variables": {"a": 1}}

    column = ProjectColumn(name="Todo")
    column.cards.append(ProjectCard(note="Task"))
    assert column.has_card("Task") is True
    assert column.has_card("Missing") is False

    board = ProjectBoard(id="id", columns=[column])
    assert board.column_by_name("Todo") is column
    assert board.column_by_name("Done") is None


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
def test_fetch_and_mutations_with_stub_client() -> None:
    """Board parsing and mutation helpers operate on typed responses."""

    responses_iter = iter(
        [
            StubResponse(
                {
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
                                                "nodes": [
                                                    {"id": "card1", "note": "Existing"}
                                                ]
                                            },
                                        }
                                    ]
                                },
                            }
                        }
                    }
                }
            ),
            StubResponse(
                {
                    "data": {
                        "addProjectColumn": {"column": {"id": "col2", "name": "Done"}}
                    }
                }
            ),
            StubResponse(
                {
                    "data": {
                        "addProjectCard": {
                            "cardEdge": {"node": {"id": "card2", "note": "New task"}}
                        }
                    }
                }
            ),
        ]
    )
    stub_client = StubHTTPClient(responses_iter)
    adapter = GitHubProjectAdapter(
        "token",
        "org",
        99,
        http_client=stub_client,
    )

    board = ProjectBoard(
        id="proj1",
        columns=[
            ProjectColumn(
                name="Todo",
                id="col1",
                cards=[ProjectCard(note="Existing", id="card1")],
            ),
            ProjectColumn(name="Done", cards=[ProjectCard(note="New task")]),
        ],
    )

    adapter.sync_board(board)

    assert [req.query for req in stub_client.captured] == [
        adapter._PROJECT_QUERY,
        adapter._ADD_COLUMN_MUTATION,
        adapter._ADD_CARD_MUTATION,
    ]


@pytest.mark.fast
def test_graphql_missing_data_raises() -> None:
    """Missing data sections raise a typed project error."""

    stub_client = StubHTTPClient(iter([StubResponse({"data": None})]))
    adapter = GitHubProjectAdapter(
        "token",
        "org",
        1,
        http_client=stub_client,
    )

    with pytest.raises(GitHubProjectError):
        adapter._graphql(GraphQLRequest(query="query { noop }", variables={}))


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


@pytest.mark.fast
def test_graphql_error_formatting_handles_missing_messages() -> None:
    """Error formatting tolerates GraphQL entries without message fields."""

    stub_client = StubHTTPClient(
        iter(
            [
                StubResponse(
                    {
                        "errors": [
                            {"message": "explicit"},
                            {"code": "missing_message"},
                        ]
                    }
                )
            ]
        )
    )
    adapter = GitHubProjectAdapter(
        "token",
        "org",
        1,
        http_client=stub_client,
    )

    with pytest.raises(GitHubProjectError) as excinfo:
        adapter._graphql(GraphQLRequest(query="query { noop }", variables={}))

    message = str(excinfo.value)
    assert "explicit" in message
    assert "<unknown error>" in message
