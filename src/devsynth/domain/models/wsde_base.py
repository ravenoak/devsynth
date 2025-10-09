"""Base WSDE classes and core team functionality.

This module contains the base WSDE class and core :class:`WSDETeam`
functionality including initialization, agent management, and messaging.
Historically the implementation leaned heavily on ``Any`` which made both the
runtime behaviour and the coupling with the optional collaboration helpers hard
to reason about.  The goal of this module is therefore twofold:

* expose a predictable, typed surface that higher level orchestration logic can
  rely on; and
* provide lifecycle hooks that gracefully initialise optional attributes even
  when the wider collaboration stack is not available.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, TypedDict, cast, runtime_checkable
from uuid import uuid4

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class TeamMessage(TypedDict):
    """Serialised representation of a team message.

    The schema is intentionally small so that tests can reason about the
    structure without requiring the full message protocol implementation.
    """

    id: str
    timestamp: datetime
    sender: str
    recipients: list[str]
    type: str
    subject: str
    content: Any
    metadata: dict[str, Any]


class RequirementReasoningRecord(TypedDict):
    """Captured output from requirement evaluation hooks."""

    reasoning: Any
    consensus: bool


class PeerReviewRequest(TypedDict):
    """Shape of the structure returned by peer review helpers."""

    id: str
    timestamp: datetime
    work_product: dict[str, Any]
    author: str
    reviewers: list[str]
    status: str
    reviews: list[Any]


@runtime_checkable
class TeamAgentLike(Protocol):
    """Protocol describing the small surface consumed by :class:`WSDETeam`."""

    name: str

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - runtime typing
        ...


@dataclass
class WSDE:
    """
    Base class for Worker Self-Directed Enterprise (WSDE) components.

    This class serves as a foundation for WSDE-related classes and provides
    basic functionality for tracking metadata and timestamps.
    """

    name: str
    description: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at


class WSDETeam:
    """
    Worker Self-Directed Enterprise (WSDE) Team implementation.

    This class implements a non-hierarchical, collaborative team structure
    based on WSDE principles. It supports dynamic role assignment, peer-based
    collaboration, and democratic decision-making processes.

    Core functionality includes:
    - Agent management (adding agents to the team)
    - Role assignment and rotation
    - Messaging between team members
    - Peer review processes

    Additional functionality like expertise calculation, voting, dialectical
    reasoning, etc. is implemented in specialized modules. The team may be
    initialized with an iterable of agents which are added during construction.
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        agents: Iterable[TeamAgentLike] | None = None,
    ) -> None:
        """Initialize a new WSDE Team.

        Args:
            name: The name of the team
            description: Optional description of the team's purpose
            agents: Optional iterable of agents to populate the team
        """
        self.name: str = name
        self.description: str | None = description
        self.agents: list[TeamAgentLike] = []
        self.roles: dict[str, TeamAgentLike | None] = {
            "primus": None,
            "worker": None,
            "supervisor": None,
            "designer": None,
            "evaluator": None,
        }
        self.messages: list[TeamMessage] = []
        # Message protocol is initialised lazily to avoid heavy imports when not
        # required. The attribute is declared here so that callers may inspect
        # or replace it even before the first message is sent.
        self.message_protocol: Any | None = None
        self.memory_manager: Any | None = None
        self.solutions: list[dict[str, Any]] = []
        self.dialectical_hooks: list[
            Callable[[dict[str, Any], Sequence[dict[str, Any]]], Any]
        ] = []
        self.voting_history: list[dict[str, Any]] = []
        # Stores results from requirement dialectical evaluations
        self.requirement_reasoning_results: list[RequirementReasoningRecord] = []
        self.knowledge_graph: Any | None = None
        self.standards: Any | None = None
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.team_id = str(uuid4())
        self.primus_index: int = 0

        # Initialize logger
        self.logger = logger
        self.logger.info(f"Created WSDE Team: {name}")

        if agents:
            self.add_agents(list(agents))

    def __post_init__(self) -> None:
        """
        Post-initialization setup.

        This method is called after the object is initialized to perform
        additional setup tasks.
        """
        # Ensure all required attributes are initialized
        if not hasattr(self, "agents"):
            self.agents = []

        if not hasattr(self, "roles"):
            self.roles = {
                "primus": None,
                "worker": None,
                "supervisor": None,
                "designer": None,
                "evaluator": None,
            }

        if not hasattr(self, "messages"):
            self.messages = []

        if not hasattr(self, "solutions"):
            self.solutions = []

        if not hasattr(self, "dialectical_hooks"):
            self.dialectical_hooks = []

        if not hasattr(self, "voting_history"):
            self.voting_history = []

        if not hasattr(self, "requirement_reasoning_results"):
            self.requirement_reasoning_results = []

        if not hasattr(self, "team_id"):
            self.team_id = str(uuid4())

        if not hasattr(self, "knowledge_graph"):
            self.knowledge_graph = None

        if not hasattr(self, "standards"):
            self.standards = None

        if not hasattr(self, "message_protocol"):
            self.message_protocol = None
        if not hasattr(self, "memory_manager"):
            self.memory_manager = None

    def add_agent(self, agent: TeamAgentLike) -> None:
        """
        Add an agent to the team.

        Args:
            agent: The agent to add to the team
        """
        self.agents.append(agent)
        agent_name = getattr(agent, "name", getattr(agent, "id", "unknown"))
        self.logger.info(f"Added agent {agent_name} to team {self.name}")

    def add_agents(self, agents: Iterable[TeamAgentLike]) -> None:
        """
        Add multiple agents to the team.

        Args:
            agents: List of agents to add to the team
        """
        for agent in agents:
            self.add_agent(agent)

    def register_dialectical_hook(
        self,
        hook: Callable[[dict[str, Any], Sequence[dict[str, Any]]], Any],
    ) -> None:
        """
        Register a hook to be called when dialectical reasoning is applied.

        Args:
            hook: A callable that takes a task and a list of solutions
        """
        self.dialectical_hooks.append(hook)
        self.logger.info(f"Registered dialectical hook in team {self.name}")

    def requirement_evaluation_hook(self, reasoning: Any, consensus: bool) -> None:
        """Record requirement dialectical reasoning results.

        Args:
            reasoning: The ``DialecticalReasoning`` object produced by the
                evaluator.
            consensus: Whether the evaluation reached consensus.
        """
        self.requirement_reasoning_results.append(
            {"reasoning": reasoning, "consensus": consensus}
        )

    def send_message(
        self,
        sender: str,
        recipients: Sequence[str],
        message_type: str,
        subject: str = "",
        content: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> TeamMessage:
        """
        Send a message from one agent to specific recipients.

        Args:
            sender: The name of the sending agent
            recipients: List of recipient agent names
            message_type: Type of message (e.g., "request", "response", "notification")
            subject: Optional subject line for the message
            content: The content of the message
            metadata: Optional metadata for the message
        """
        # Delegate to the shared message protocol if available. This ensures
        # messages are persisted and optionally synchronised with the memory
        # manager.  The protocol is initialised lazily by the utility helper so
        # importing here avoids a hard dependency during module import.
        try:
            from . import wsde_utils as _utils

            if getattr(self, "message_protocol", None) is None:
                try:
                    from devsynth.application.collaboration.message_protocol import (
                        MessageProtocol,
                    )

                    self.message_protocol = MessageProtocol(
                        memory_manager=getattr(self, "memory_manager", None)
                    )
                except Exception:  # pragma: no cover - message protocol optional
                    self.message_protocol = None
            elif (
                self.message_protocol is not None
                and getattr(self, "memory_manager", None) is not None
                and getattr(self.message_protocol, "memory_manager", None) is None
            ):
                try:  # pragma: no cover - defensive
                    self.message_protocol.memory_manager = self.memory_manager
                except Exception:
                    pass

            proto_msg = _utils.send_message(
                self,
                sender,
                recipients,
                message_type,
                subject,
                content,
                metadata,
            )
        except Exception:  # pragma: no cover - best effort fallback
            proto_msg = None

        if proto_msg is not None:
            message: TeamMessage = {
                "id": proto_msg.message_id,
                "timestamp": proto_msg.timestamp,
                "sender": proto_msg.sender,
                "recipients": list(proto_msg.recipients),
                "type": proto_msg.message_type.value,
                "subject": proto_msg.subject,
                "content": proto_msg.content,
                "metadata": dict(proto_msg.metadata or {}),
            }
        else:
            # Fallback to in-memory message if the protocol is unavailable.
            message = cast(
                TeamMessage,
                {
                    "id": str(uuid4()),
                    "timestamp": datetime.now(),
                    "sender": sender,
                    "recipients": list(recipients),
                    "type": message_type,
                    "subject": subject,
                    "content": content,
                    "metadata": dict(metadata or {}),
                },
            )

        self.messages.append(message)
        self.logger.debug(f"Message sent from {sender} to {recipients}: {subject}")
        return message

    def broadcast_message(
        self,
        sender: str,
        message_type: str,
        subject: str = "",
        content: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> TeamMessage:
        """
        Broadcast a message from one agent to all team members.

        Args:
            sender: The name of the sending agent
            message_type: Type of message (e.g., "announcement", "notification")
            subject: Optional subject line for the message
            content: The content of the message
            metadata: Optional metadata for the message
        """
        recipients = [
            getattr(agent, "name", getattr(agent, "id", "unknown"))
            for agent in self.agents
            if getattr(agent, "name", getattr(agent, "id", None)) != sender
        ]
        message = self.send_message(
            sender=sender,
            recipients=recipients,
            message_type=message_type,
            subject=subject,
            content=content,
            metadata=metadata,
        )
        self.logger.debug(f"Broadcast message sent from {sender}: {subject}")
        return message

    def get_messages(
        self,
        agent: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[TeamMessage]:
        """
        Get messages for a specific agent or with specific filters.

        Args:
            agent: Optional agent name to filter messages for
            filters: Optional dictionary of filters to apply

        Returns:
            List of messages matching the criteria
        """
        filtered_messages: list[TeamMessage] = list(self.messages)

        if agent:
            filtered_messages = [
                m
                for m in filtered_messages
                if agent in m["recipients"] or m["sender"] == agent
            ]

        if filters:
            for key, value in filters.items():
                filtered_messages = [
                    m for m in filtered_messages if m.get(key) == value
                ]

        return filtered_messages

    def request_peer_review(
        self,
        work_product: dict[str, Any],
        author: TeamAgentLike,
        reviewer_agents: Sequence[TeamAgentLike],
    ) -> PeerReviewRequest:
        """
        Request peer review for a work product.

        Args:
            work_product: The work product to be reviewed
            author: The agent who created the work product
            reviewer_agents: List of agents to review the work product

        Returns:
            Dictionary containing the review request details
        """
        author_name = getattr(author, "name", getattr(author, "id", "unknown"))
        reviewer_names = [
            getattr(agent, "name", getattr(agent, "id", "unknown"))
            for agent in reviewer_agents
        ]

        review_request: PeerReviewRequest = {
            "id": str(uuid4()),
            "timestamp": datetime.now(),
            "work_product": work_product,
            "author": author_name,
            "reviewers": reviewer_names,
            "status": "requested",
            "reviews": [],
        }

        # Send messages to reviewers
        for reviewer in reviewer_agents:
            reviewer_name = getattr(
                reviewer, "name", getattr(reviewer, "id", "unknown")
            )
            self.send_message(
                sender=author_name,
                recipients=[reviewer_name],
                message_type="review_request",
                subject=f"Review request for {work_product.get('title', 'work product')}",
                content=work_product,
                metadata={"review_id": review_request["id"]},
            )

        self.logger.info(
            f"Peer review requested by {author_name} for {len(reviewer_agents)} reviewers"
        )
        return review_request

    def conduct_peer_review(
        self,
        work_product: dict[str, Any],
        author: TeamAgentLike,
        reviewer_agents: Sequence[TeamAgentLike],
    ) -> PeerReviewRequest:
        """
        Conduct a peer review process for a work product.

        Args:
            work_product: The work product to be reviewed
            author: The agent who created the work product
            reviewer_agents: List of agents to review the work product

        Returns:
            Dictionary containing the review results
        """
        review_request = self.request_peer_review(work_product, author, reviewer_agents)
        # In a real implementation, this would wait for reviews to be submitted
        # For now, we'll just return the review request
        author_name = getattr(author, "name", getattr(author, "id", "unknown"))
        self.logger.info(
            f"Peer review process initiated for work product from {author_name}"
        )
        return review_request

    def rotate_primus(self) -> TeamAgentLike | None:
        """
        Rotate the primus role to the next agent in the team.

        Returns:
            The new primus agent or None if no agents are available
        """
        if not self.agents:
            self.logger.warning("Cannot rotate primus: no agents in team")
            return None

        current = self.roles.get("primus")
        if current in self.agents:
            idx = self.agents.index(current)
        else:
            idx = -1

        next_idx = (idx + 1) % len(self.agents)
        next_agent = self.agents[next_idx]
        self.roles["primus"] = next_agent

        # Inline role update logic to avoid a runtime import of ``wsde_roles``
        # which previously created a circular dependency during module
        # initialization.
        setattr(next_agent, "previous_role", getattr(next_agent, "current_role", None))
        setattr(next_agent, "current_role", "Primus")
        if next_agent in self.agents:
            self.primus_index = self.agents.index(next_agent)
            setattr(next_agent, "has_been_primus", True)

        if all(getattr(a, "has_been_primus", False) for a in self.agents):
            for a in self.agents:
                if a is not next_agent:
                    setattr(a, "has_been_primus", False)

        primus_name = getattr(next_agent, "name", getattr(next_agent, "id", "unknown"))
        self.logger.info(f"Rotated primus role to {primus_name}")
        return next_agent

    def get_primus(self) -> TeamAgentLike | None:
        """
        Get the current primus agent.

        Returns:
            The current primus agent or None if not assigned
        """
        return self.roles.get("primus")

    def get_worker(self) -> TeamAgentLike | None:
        """
        Get the current worker agent.

        Returns:
            The current worker agent or None if not assigned
        """
        return self.roles.get("worker")

    def get_supervisor(self) -> TeamAgentLike | None:
        """
        Get the current supervisor agent.

        Returns:
            The current supervisor agent or None if not assigned
        """
        return self.roles.get("supervisor")

    def get_designer(self) -> TeamAgentLike | None:
        """
        Get the current designer agent.

        Returns:
            The current designer agent or None if not assigned
        """
        return self.roles.get("designer")

    def get_evaluator(self) -> TeamAgentLike | None:
        """
        Get the current evaluator agent.

        Returns:
            The current evaluator agent or None if not assigned
        """
        return self.roles.get("evaluator")

    def set_knowledge_graph(self, graph: Any) -> None:
        """Attach a knowledge graph to the team for later use."""
        self.knowledge_graph = graph
        self.logger.info("Knowledge graph set for team %s", self.name)

    def set_standards(self, standards: Any) -> None:
        """Attach standards and best practices to the team."""
        self.standards = standards
        self.logger.info("Standards set for team %s", self.name)
