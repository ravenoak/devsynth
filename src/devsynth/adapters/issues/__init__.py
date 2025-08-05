"""Issue tracking adapters."""

from .github_adapter import GitHubIssueAdapter
from .jira_adapter import JiraIssueAdapter

__all__ = ["GitHubIssueAdapter", "JiraIssueAdapter"]
