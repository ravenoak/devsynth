"""Jira issue metadata adapter."""

from __future__ import annotations

from typing import Dict, Optional

import requests

from devsynth.logging_setup import DevSynthLogger


class JiraIssueAdapter:
    """Adapter for fetching issue metadata from Jira."""

    def __init__(self, base_url: str, token: str) -> None:
        """Initialize the adapter with authentication details.

        Args:
            base_url: Base URL of the Jira instance, e.g.
                ``https://jira.example.com``.
            token: API token or bearer token for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.logger = DevSynthLogger(__name__)

    def fetch(self, issue_key: str) -> dict[str, str] | None:
        """Fetch title and acceptance criteria for the given issue key.

        Args:
            issue_key: Jira issue key such as ``"PROJ-123"``.

        Returns:
            Mapping with ``title`` and ``acceptance_criteria`` if successful,
            otherwise ``None``.
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network failure
            self.logger.error("Jira issue fetch failed: %s", exc)
            return None
        data = resp.json()
        fields = data.get("fields", {})
        title = fields.get("summary", "")
        description = fields.get("description", "") or ""
        return {"title": title, "acceptance_criteria": description}
