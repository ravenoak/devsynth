"""GitHub issue metadata adapter."""

from __future__ import annotations

from typing import Dict, Optional

import requests

from devsynth.logging_setup import DevSynthLogger


class GitHubIssueAdapter:
    """Adapter for fetching issue metadata from GitHub."""

    def __init__(self, base_url: str, token: str) -> None:
        """Initialize the adapter with authentication details.

        Args:
            base_url: Base API URL for the repository, e.g.
                ``https://api.github.com/repos/org/repo``.
            token: Personal access token used for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.logger = DevSynthLogger(__name__)

    def fetch(self, issue_ref: str) -> dict[str, str] | None:
        """Fetch title and acceptance criteria for the given issue.

        Args:
            issue_ref: Issue reference such as ``"#123"`` or ``"123"``.

        Returns:
            Mapping with ``title`` and ``acceptance_criteria`` if successful,
            otherwise ``None``.
        """
        issue_number = issue_ref.lstrip("#")
        url = f"{self.base_url}/issues/{issue_number}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            self.logger.error("GitHub issue fetch failed: %s", exc)
            return None
        if resp.status_code != 200:
            self.logger.error("GitHub issue fetch failed: HTTP %s", resp.status_code)
            return None
        data = resp.json()
        title = data.get("title", "")
        body = data.get("body", "") or ""
        return {"title": title, "acceptance_criteria": body}
