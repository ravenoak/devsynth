"""Tests for the GitHubIssueAdapter."""

import responses

from devsynth.adapters.issues import GitHubIssueAdapter


@responses.activate
def test_fetch_github_issue() -> None:
    """Adapter returns title and body from the GitHub API."""
    adapter = GitHubIssueAdapter("https://api.github.com/repos/org/repo", "token")
    responses.add(
        responses.GET,
        "https://api.github.com/repos/org/repo/issues/1",
        json={"title": "Bug fix", "body": "do things"},
        status=200,
    )
    data = adapter.fetch("#1")
    assert data == {"title": "Bug fix", "acceptance_criteria": "do things"}
