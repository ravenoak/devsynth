"""Tests for the JiraAdapter."""

import json

import responses

from devsynth.adapters.jira_adapter import JiraAdapter


@responses.activate
def test_create_issue() -> None:
    """Adapter posts issue data and returns created key."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    responses.add(
        responses.POST,
        "https://example.atlassian.net/rest/api/3/issue",
        json={"key": "TEST-1"},
        status=201,
    )
    key = adapter.create_issue("Bug", "details")
    assert key == "TEST-1"
    body = json.loads(responses.calls[0].request.body)
    assert body["fields"]["summary"] == "Bug"
    assert body["fields"]["description"] == "details"
    assert body["fields"]["project"]["key"] == "TEST"


@responses.activate
def test_transition_issue() -> None:
    """Adapter retrieves transitions and posts selected transition."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    responses.add(
        responses.GET,
        "https://example.atlassian.net/rest/api/3/issue/TEST-1/transitions",
        json={"transitions": [{"id": "1", "name": "Done"}]},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://example.atlassian.net/rest/api/3/issue/TEST-1/transitions",
        status=204,
    )
    adapter.transition_issue("TEST-1", "Done")
    assert len(responses.calls) == 2
    post_body = json.loads(responses.calls[1].request.body)
    assert post_body["transition"]["id"] == "1"
