"""GitHub Project integration adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

import requests

from devsynth.logging_setup import DevSynthLogger


class GitHubProjectError(RuntimeError):
    """Raised when GitHub GraphQL responses signal an error."""


class GraphQLHTTPResponse(Protocol):
    """Minimal response protocol for the GraphQL transport."""

    def raise_for_status(self) -> None:
        """Raise HTTP errors."""

    def json(self) -> object:
        """Return the decoded JSON payload."""


class GraphQLHTTPClient(Protocol):
    """Protocol describing the HTTP client used for GraphQL requests."""

    def post(
        self,
        url: str,
        *,
        json: Mapping[str, object],
        headers: Mapping[str, str],
        timeout: int,
    ) -> GraphQLHTTPResponse:
        """Execute an HTTP POST request."""


@dataclass(frozen=True)
class GraphQLRequest:
    """Structure for serializing GraphQL requests."""

    query: str
    variables: Mapping[str, object]

    def payload(self) -> Mapping[str, object]:
        """Serialize the GraphQL request into a JSON-ready mapping."""

        return {"query": self.query, "variables": dict(self.variables)}


@dataclass(frozen=True)
class ProjectCard:
    """Represents a Project card state."""

    note: str
    id: str | None = None


@dataclass
class ProjectColumn:
    """Represents a Project column and its cards."""

    name: str
    id: str | None = None
    cards: list[ProjectCard] = field(default_factory=list)

    def has_card(self, note: str) -> bool:
        """Return whether a card with the given note already exists."""

        return any(card.note == note for card in self.cards)


@dataclass
class ProjectBoard:
    """Represents the Project board structure."""

    id: str
    columns: list[ProjectColumn] = field(default_factory=list)

    def column_by_name(self, name: str) -> ProjectColumn | None:
        """Return the column that matches ``name`` if present."""

        for column in self.columns:
            if column.name == name:
                return column
        return None


@dataclass(frozen=True)
class AddColumnVariables:
    """Variables required to add a column to a GitHub Project."""

    project_id: str
    name: str

    def to_mapping(self) -> Mapping[str, object]:
        """Serialize the variables for GraphQL."""

        return {"projectId": self.project_id, "name": self.name}


@dataclass(frozen=True)
class AddCardVariables:
    """Variables required to add a card to a GitHub Project column."""

    column_id: str
    note: str

    def to_mapping(self) -> Mapping[str, object]:
        """Serialize the variables for GraphQL."""

        return {"columnId": self.column_id, "note": self.note}


class RequestsHTTPClient:
    """Thin wrapper adapting :mod:`requests` to the GraphQL client protocol."""

    def __init__(self) -> None:
        self._session: requests.Session = requests.Session()

    def post(
        self,
        url: str,
        *,
        json: Mapping[str, object],
        headers: Mapping[str, str],
        timeout: int,
    ) -> GraphQLHTTPResponse:
        return self._session.post(url, json=json, headers=headers, timeout=timeout)


class GitHubProjectAdapter:
    """Adapter for synchronizing DevSynth tasks with GitHub Projects boards."""

    _PROJECT_QUERY = """
    query($org: String!, $number: Int!) {
        organization(login: $org) {
            project(number: $number) {
                id
                columns(first: 100) {
                    nodes {
                        id
                        name
                        cards(first: 100) { nodes { id note } }
                    }
                }
            }
        }
    }
    """

    _ADD_COLUMN_MUTATION = """
    mutation($projectId: ID!, $name: String!) {
        addProjectColumn(input: {projectId: $projectId, name: $name}) {
            column { id name }
        }
    }
    """

    _ADD_CARD_MUTATION = """
    mutation($columnId: ID!, $note: String!) {
        addProjectCard(input: {columnId: $columnId, note: $note}) {
            cardEdge { node { id note } }
        }
    }
    """

    def __init__(
        self,
        token: str,
        organization: str,
        project_number: int,
        *,
        http_client: GraphQLHTTPClient | None = None,
    ) -> None:
        """Initialize the adapter with authentication details.

        Args:
            token: GitHub personal access token.
            organization: GitHub organization name.
            project_number: Numeric identifier of the project board.
            http_client: Optional HTTP client implementing :class:`GraphQLHTTPClient`.
        """

        self.organization = organization
        self.project_number = project_number
        self.logger = DevSynthLogger(__name__)
        self._endpoint = "https://api.github.com/graphql"
        self._headers: Mapping[str, str] = {"Authorization": f"bearer {token}"}
        self._http_client = http_client or RequestsHTTPClient()

    def _graphql(self, request: GraphQLRequest) -> Mapping[str, object]:
        """Execute a GraphQL request and return the data section."""

        response = self._http_client.post(
            self._endpoint,
            json=request.payload(),
            headers=self._headers,
            timeout=10,
        )
        response.raise_for_status()
        payload_raw: object = response.json()
        payload = self._expect_mapping(payload_raw, "GraphQL response")

        errors = payload.get("errors")
        if errors is not None:
            error_messages = ", ".join(self._format_error_messages(errors))
            raise GitHubProjectError(f"GitHub GraphQL error: {error_messages}")

        data = payload.get("data")
        if data is None:
            raise GitHubProjectError("GitHub GraphQL payload missing 'data'")
        return self._expect_mapping(data, "GraphQL response data")

    def sync_board(self, board_state: ProjectBoard) -> None:
        """Synchronize the local board state with GitHub Projects."""

        remote_board = self._fetch_board()

        for column_state in board_state.columns:
            column = remote_board.column_by_name(column_state.name)
            if column is None:
                column = self._create_column(remote_board.id, column_state.name)
                remote_board.columns.append(column)

            column_id = column.id
            if column_id is None:
                raise GitHubProjectError(
                    f"Column '{column.name}' is missing an identifier in the remote board"
                )

            for card_state in column_state.cards:
                if column.has_card(card_state.note):
                    continue
                self._create_card(column_id, card_state.note)
                column.cards.append(ProjectCard(note=card_state.note))

    def _fetch_board(self) -> ProjectBoard:
        variables: Mapping[str, object] = {
            "org": self.organization,
            "number": self.project_number,
        }
        data = self._graphql(
            GraphQLRequest(query=self._PROJECT_QUERY, variables=variables)
        )

        organization = self._expect_mapping(
            data.get("organization"), "GraphQL project organization"
        )
        project = self._expect_mapping(
            organization.get("project"), "GraphQL project payload"
        )

        project_id = self._expect_str(project.get("id"), "project.id")

        columns_container = self._expect_mapping(
            project.get("columns"), "project.columns"
        )
        columns_nodes = self._expect_sequence(
            columns_container.get("nodes"), "project.columns.nodes"
        )

        columns: list[ProjectColumn] = []
        for column_node_obj in columns_nodes:
            column_node = self._expect_mapping(column_node_obj, "project column node")
            column_id = self._expect_str(column_node.get("id"), "column.id")
            column_name = self._expect_str(column_node.get("name"), "column.name")

            cards_container = self._expect_mapping(
                column_node.get("cards"), "column.cards"
            )
            card_nodes = self._expect_sequence(
                cards_container.get("nodes"), "column.cards.nodes"
            )

            cards: list[ProjectCard] = []
            for card_node_obj in card_nodes:
                card_node = self._expect_mapping(card_node_obj, "card node")
                card_id = self._expect_str(card_node.get("id"), "card.id")
                card_note = self._expect_str(card_node.get("note"), "card.note")
                cards.append(ProjectCard(note=card_note, id=card_id))

            columns.append(ProjectColumn(name=column_name, id=column_id, cards=cards))

        return ProjectBoard(id=project_id, columns=columns)

    def _create_column(self, project_id: str, name: str) -> ProjectColumn:
        variables = AddColumnVariables(project_id=project_id, name=name).to_mapping()
        data = self._graphql(
            GraphQLRequest(query=self._ADD_COLUMN_MUTATION, variables=variables)
        )
        mutation_root = self._expect_mapping(
            data.get("addProjectColumn"), "addProjectColumn payload"
        )
        column_node = self._expect_mapping(
            mutation_root.get("column"), "addProjectColumn.column"
        )
        column_id = self._expect_str(
            column_node.get("id"), "addProjectColumn.column.id"
        )
        column_name = self._expect_str(
            column_node.get("name"), "addProjectColumn.column.name"
        )
        return ProjectColumn(name=column_name, id=column_id)

    def _create_card(self, column_id: str, note: str) -> None:
        variables = AddCardVariables(column_id=column_id, note=note).to_mapping()
        data = self._graphql(
            GraphQLRequest(query=self._ADD_CARD_MUTATION, variables=variables)
        )
        mutation_root = self._expect_mapping(
            data.get("addProjectCard"), "addProjectCard payload"
        )
        card_edge = self._expect_mapping(
            mutation_root.get("cardEdge"), "addProjectCard.cardEdge"
        )
        node = self._expect_mapping(
            card_edge.get("node"), "addProjectCard.cardEdge.node"
        )
        # Ensure the response contained the expected identifiers.
        self._expect_str(node.get("id"), "addProjectCard.cardEdge.node.id")
        self._expect_str(node.get("note"), "addProjectCard.cardEdge.node.note")

    def _expect_mapping(self, value: object, context: str) -> Mapping[str, object]:
        if not isinstance(value, Mapping):
            raise GitHubProjectError(
                f"Expected mapping for {context}, received {type(value)!r}"
            )
        return value

    def _expect_sequence(self, value: object, context: str) -> Sequence[object]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise GitHubProjectError(
                f"Expected sequence for {context}, received {type(value)!r}"
            )
        return value

    def _expect_str(self, value: object | None, context: str) -> str:
        if not isinstance(value, str):
            raise GitHubProjectError(
                f"Expected string for {context}, received {type(value)!r}"
            )
        return value

    def _format_error_messages(self, errors: object) -> Sequence[str]:
        error_seq = self._expect_sequence(errors, "GraphQL errors")
        messages: list[str] = []
        for error_obj in error_seq:
            error_mapping = self._expect_mapping(error_obj, "GraphQL error")
            message = error_mapping.get("message")
            if isinstance(message, str):
                messages.append(message)
            else:
                messages.append("<unknown error>")
        return messages
