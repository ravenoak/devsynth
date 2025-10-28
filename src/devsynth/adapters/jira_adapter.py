"""Jira integration adapter."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol, TypedDict, cast, runtime_checkable
from collections.abc import Iterable

import requests

from devsynth.logging_setup import DevSynthLogger


@dataclass(frozen=True)
class JiraProjectReference:
    """Reference to a Jira project."""

    key: str


@dataclass(frozen=True)
class JiraIssueType:
    """Jira issue type descriptor."""

    name: str


@dataclass(frozen=True)
class JiraIssueFields:
    """Fields required for creating a Jira issue."""

    project: JiraProjectReference
    summary: str
    description: str
    issuetype: JiraIssueType


@dataclass(frozen=True)
class JiraIssueCreatePayload:
    """Payload wrapper for Jira issue creation."""

    fields: JiraIssueFields

    def to_dict(self) -> dict[str, Any]:
        """Convert the payload to a serializable mapping."""

        return asdict(self)


@dataclass(frozen=True)
class JiraTransition:
    """Transition descriptor for Jira issues."""

    id: str


@dataclass(frozen=True)
class JiraTransitionPayload:
    """Payload wrapper for transitioning a Jira issue."""

    transition: JiraTransition

    def to_dict(self) -> dict[str, Any]:
        """Convert the transition payload to a serializable mapping."""

        return asdict(self)


class JiraIssueCreateResponse(TypedDict):
    """Response payload for Jira issue creation."""

    key: str


class JiraTransitionDescriptor(TypedDict):
    """Descriptor for an available Jira transition."""

    id: str
    name: str


class JiraTransitionsResponse(TypedDict, total=False):
    """Response payload describing available Jira transitions."""

    transitions: list[JiraTransitionDescriptor]


@runtime_checkable
class HTTPResponseProtocol(Protocol):
    """Protocol describing the subset of response behaviour used by the adapter."""

    def raise_for_status(self) -> None:
        """Raise an exception if the HTTP response indicates a failure."""

    def json(self) -> Any:
        """Return the JSON body of the response."""


@runtime_checkable
class HTTPClientProtocol(Protocol):
    """Protocol describing the HTTP client interface used by the adapter."""

    def post(self, url: str, **kwargs: Any) -> HTTPResponseProtocol:
        """Send an HTTP POST request."""

    def get(self, url: str, **kwargs: Any) -> HTTPResponseProtocol:
        """Send an HTTP GET request."""


class JiraAdapterError(RuntimeError):
    """Base error for Jira adapter failures."""


class JiraHttpError(JiraAdapterError):
    """Error raised when an HTTP request to Jira fails."""


class JiraTransitionNotFoundError(JiraAdapterError):
    """Raised when the requested transition cannot be located."""


class JiraAdapter:
    """Adapter for interacting with Jira issues."""

    def __init__(
        self,
        url: str,
        email: str,
        token: str,
        project_key: str,
        http_client: HTTPClientProtocol | None = None,
    ) -> None:
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
        default_client: HTTPClientProtocol = cast(
            HTTPClientProtocol, requests.Session()
        )
        self.http_client = http_client if http_client is not None else default_client

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
        payload = JiraIssueCreatePayload(
            fields=JiraIssueFields(
                project=JiraProjectReference(key=self.project_key),
                summary=summary,
                description=description,
                issuetype=JiraIssueType(name=issue_type),
            )
        ).to_dict()
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        try:
            resp = self.http_client.post(
                url,
                json=payload,
                headers=headers,
                auth=(self.email, self.token),
                timeout=10,
            )
        except Exception as exc:  # pragma: no cover - network failure
            self.logger.error("Jira issue creation failed: %s", exc)
            raise JiraHttpError("Failed to submit Jira issue creation request") from exc
        try:
            resp.raise_for_status()
            data = cast(JiraIssueCreateResponse, resp.json())
        except Exception as exc:  # pragma: no cover - unexpected response
            self.logger.error("Jira issue creation failed: %s", exc)
            raise JiraHttpError(
                "Jira issue creation returned an invalid response"
            ) from exc
        key = data.get("key")
        if not key:
            message = "Jira issue creation response was missing the issue key"
            self.logger.error(message)
            raise JiraHttpError(message)
        return key

    def transition_issue(self, issue_key: str, status: str) -> None:
        """Transition an issue to a new status.

        Args:
            issue_key: Key of the issue to transition.
            status: Name of the destination status.
        """
        base = f"{self.url}/rest/api/3/issue/{issue_key}/transitions"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        try:
            resp = self.http_client.get(
                base,
                headers=headers,
                auth=(self.email, self.token),
                timeout=10,
            )
        except Exception as exc:  # pragma: no cover - network failure
            self.logger.error("Fetching Jira transitions failed: %s", exc)
            raise JiraHttpError("Failed to request Jira transitions") from exc
        try:
            resp.raise_for_status()
            transitions_data = cast(JiraTransitionsResponse, resp.json())
        except Exception as exc:  # pragma: no cover - unexpected response
            self.logger.error("Fetching Jira transitions failed: %s", exc)
            raise JiraHttpError("Failed to parse Jira transitions response") from exc
        transitions = transitions_data.get("transitions")
        if not transitions:
            message = f"Transition '{status}' not found for issue {issue_key}"
            self.logger.error(message)
            raise JiraTransitionNotFoundError(message)
        transition_id = self._find_transition_id(transitions, status, issue_key)
        payload = JiraTransitionPayload(
            transition=JiraTransition(id=transition_id)
        ).to_dict()
        try:
            resp = self.http_client.post(
                base,
                json=payload,
                headers=headers,
                auth=(self.email, self.token),
                timeout=10,
            )
        except Exception as exc:  # pragma: no cover - network failure
            self.logger.error("Jira issue transition failed: %s", exc)
            raise JiraHttpError("Failed to submit Jira transition request") from exc
        try:
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - unexpected response
            self.logger.error("Jira issue transition failed: %s", exc)
            raise JiraHttpError("Jira transition request returned an error") from exc

    def _find_transition_id(
        self,
        transitions: Iterable[JiraTransitionDescriptor],
        status: str,
        issue_key: str,
    ) -> str:
        """Locate the transition identifier for the requested status."""

        desired = status.lower()
        for transition in transitions:
            try:
                name = transition["name"]
                transition_id = transition["id"]
            except KeyError as exc:
                message = "Transition payload missing required fields"
                self.logger.error(message)
                raise JiraHttpError(message) from exc
            if name.lower() == desired:
                return transition_id
        message = f"Transition '{status}' not found for issue {issue_key}"
        self.logger.error(message)
        raise JiraTransitionNotFoundError(message)
