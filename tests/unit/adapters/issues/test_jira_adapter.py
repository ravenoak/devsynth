"""Tests for the JiraIssueAdapter."""

import responses

from devsynth.adapters.issues import JiraIssueAdapter


@responses.activate
def test_fetch_jira_issue() -> None:
    """Adapter returns title and description from the Jira API."""
    adapter = JiraIssueAdapter("https://jira.example.com", "token")
    responses.add(
        responses.GET,
        "https://jira.example.com/rest/api/2/issue/PROJ-1",
        json={"fields": {"summary": "Bug", "description": "criteria"}},
        status=200,
    )
    data = adapter.fetch("PROJ-1")
    assert data == {"title": "Bug", "acceptance_criteria": "criteria"}
