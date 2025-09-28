"""Tests for the JiraAdapter."""

from __future__ import annotations

import json

import pytest
import responses
from requests import HTTPError

from devsynth.adapters.jira_adapter import JiraAdapter


@pytest.mark.fast
@responses.activate
def test_create_issue_payload_serialization() -> None:
    """Adapter posts dataclass-serialized payload matching Jira schema."""
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
    assert body == {
        "fields": {
            "project": {"key": "TEST"},
            "summary": "Bug",
            "description": "details",
            "issuetype": {"name": "Task"},
        }
    }


@pytest.mark.fast
@responses.activate
def test_transition_issue_missing_status() -> None:
    """Transitioning with a missing status raises a ValueError."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    responses.add(
        responses.GET,
        "https://example.atlassian.net/rest/api/3/issue/TEST-1/transitions",
        json={"transitions": [{"id": "1", "name": "In Progress"}]},
        status=200,
    )

    with pytest.raises(ValueError):
        adapter.transition_issue("TEST-1", "Done")


@pytest.mark.fast
@responses.activate
def test_create_issue_http_error_surfaced() -> None:
    """HTTP errors are surfaced to the caller during issue creation."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    responses.add(
        responses.POST,
        "https://example.atlassian.net/rest/api/3/issue",
        json={"error": "bad"},
        status=400,
    )

    with pytest.raises(HTTPError):
        adapter.create_issue("Bug", "details")
