"""Tests for the JiraAdapter."""

from __future__ import annotations

import json

import pytest
import responses

from devsynth.adapters.jira_adapter import (
    JiraAdapter,
    JiraHttpError,
    JiraTransitionNotFoundError,
)


@pytest.mark.fast
def test_create_issue_payload_serialization() -> None:
    """Adapter posts dataclass-serialized payload matching Jira schema."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.POST,
            "https://example.atlassian.net/rest/api/3/issue",
            json={"key": "TEST-1"},
            status=201,
        )
        key = adapter.create_issue("Bug", "details")
        assert key == "TEST-1"
        body_raw = rsps.calls[0].request.body
        assert body_raw is not None
        body = json.loads(body_raw)
    assert body == {
        "fields": {
            "project": {"key": "TEST"},
            "summary": "Bug",
            "description": "details",
            "issuetype": {"name": "Task"},
        }
    }


@pytest.mark.fast
def test_transition_issue_missing_status() -> None:
    """Transitioning with a missing status raises the adapter's error."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            "https://example.atlassian.net/rest/api/3/issue/TEST-1/transitions",
            json={"transitions": [{"id": "1", "name": "In Progress"}]},
            status=200,
        )

        with pytest.raises(JiraTransitionNotFoundError):
            adapter.transition_issue("TEST-1", "Done")


@pytest.mark.fast
def test_create_issue_http_error_surfaced(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """HTTP errors raise JiraHttpError and are logged."""
    adapter = JiraAdapter(
        url="https://example.atlassian.net",
        email="user@example.com",
        token="token",
        project_key="TEST",
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.POST,
            "https://example.atlassian.net/rest/api/3/issue",
            json={"error": "bad"},
            status=400,
        )

        with pytest.raises(JiraHttpError):
            adapter.create_issue("Bug", "details")
    assert "Jira issue creation failed" in caplog.text
