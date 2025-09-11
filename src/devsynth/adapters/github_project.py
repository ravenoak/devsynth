"""GitHub Project integration adapter."""

from typing import Any, Dict

import requests

from devsynth.logging_setup import DevSynthLogger


class GitHubProjectAdapter:
    """Adapter for synchronizing DevSynth tasks with GitHub Projects boards."""

    def __init__(self, token: str, organization: str, project_number: int) -> None:
        """Initialize the adapter with authentication details.

        Args:
            token: GitHub personal access token.
            organization: GitHub organization name.
            project_number: Numeric identifier of the project board.
        """
        self.token = token
        self.organization = organization
        self.project_number = project_number
        self.logger = DevSynthLogger(__name__)
        self._endpoint = "https://api.github.com/graphql"
        self._headers = {"Authorization": f"bearer {token}"}

    def _graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL query against the GitHub API."""
        response = requests.post(
            self._endpoint,
            json={"query": query, "variables": variables},
            headers=self._headers,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")
        return payload["data"]

    def sync_board(self, board_state: Dict[str, Any]) -> None:
        """Synchronize the local board state with GitHub Projects.

        Args:
            board_state: Dictionary describing columns and cards to sync.
        """

        project_query = """
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
        data = self._graphql(
            project_query, {"org": self.organization, "number": self.project_number}
        )
        project = data["organization"]["project"]
        existing_columns = {c["name"]: c for c in project["columns"]["nodes"]}

        for column in board_state.get("columns", []):
            name = column["name"]
            if name in existing_columns:
                column_id = existing_columns[name]["id"]
                existing_cards = {
                    card["note"]: card
                    for card in existing_columns[name]["cards"]["nodes"]
                }
            else:
                add_column = """
                mutation($projectId: ID!, $name: String!) {
                    addProjectColumn(input: {projectId: $projectId, name: $name}) {
                        column { id }
                    }
                }
                """
                result = self._graphql(
                    add_column, {"projectId": project["id"], "name": name}
                )
                column_id = result["addProjectColumn"]["column"]["id"]
                existing_cards = {}

            for card in column.get("cards", []):
                note = card["note"]
                if note in existing_cards:
                    continue
                add_card = """
                mutation($columnId: ID!, $note: String!) {
                    addProjectCard(input: {columnId: $columnId, note: $note}) {
                        cardEdge { node { id } }
                    }
                }
                """
                self._graphql(add_card, {"columnId": column_id, "note": note})
