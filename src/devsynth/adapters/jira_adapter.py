"""Jira integration adapter."""

from __future__ import annotations

from typing import Optional

import requests

from devsynth.logging_setup import DevSynthLogger


class JiraAdapter:
    """Adapter for interacting with Jira issues."""

    def __init__(self, url: str, email: str, token: str, project_key: str) -> None:
        """Initialize the Jira adapter.

        Args:
            url: Base URL of the Jira instance.
            email: User email for authentication.
            token: API token for Jira.
            project_key: Project key to operate on.
        """
        self.url = url.rstrip("/")
        self.email = email
        self.token = token
        self.project_key = project_key
        self.logger = DevSynthLogger(__name__)

    def create_issue(
        self, summary: str, description: str, issue_type: str = "Task"
    ) -> str:
        """Create an issue in Jira and return its key.

        Args:
            summary: Summary of the issue.
            description: Detailed description of the issue.
            issue_type: Jira issue type (default ``"Task"``).

        Returns:
            The Jira issue key, e.g. ``"PROJ-1"``.
        """
        url = f"{self.url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=(self.email, self.token),
                timeout=10,
            )
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network failure
            self.logger.error("Jira issue creation failed: %s", exc)
            raise
        data = resp.json()
        return data.get("key", "")

    def transition_issue(self, issue_key: str, status: str) -> None:
        """Transition an issue to a new status.

        Args:
            issue_key: Key of the issue to transition.
            status: Name of the destination status.
        """
        base = f"{self.url}/rest/api/3/issue/{issue_key}/transitions"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        try:
            resp = requests.get(
                base,
                headers=headers,
                auth=(self.email, self.token),
                timeout=10,
            )
            resp.raise_for_status()
            transitions = resp.json().get("transitions", [])
            transition_id: Optional[str] = None
            for t in transitions:
                name = t.get("name")
                if name and name.lower() == status.lower():
                    transition_id = t.get("id")
                    break
            if transition_id is None:
                raise ValueError(f"Transition '{status}' not found")
            payload = {"transition": {"id": transition_id}}
            resp = requests.post(
                base,
                json=payload,
                headers=headers,
                auth=(self.email, self.token),
                timeout=10,
            )
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network failure
            self.logger.error("Jira issue transition failed: %s", exc)
            raise
