"""Dialectical reasoner for requirements management."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections.abc import Callable, Sequence
from uuid import UUID, uuid4

from devsynth.application.collaboration.exceptions import (
    ConsensusError as BaseConsensusError,
)
from devsynth.application.requirements.models import (
    EDRRPhase,
    ImpactNotificationPayload,
)
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.requirement import (
    ChatMessage,
    ChatSession,
    DialecticalReasoning,
    ImpactAssessment,
    Requirement,
    RequirementChange,
)
from devsynth.logging_setup import DevSynthLogger
from devsynth.ports.llm_port import LLMPort
from devsynth.ports.requirement_port import (
    ChatRepositoryPort,
    DialecticalReasonerPort,
    DialecticalReasoningRepositoryPort,
    ImpactAssessmentRepositoryPort,
    NotificationPort,
    RequirementRepositoryPort,
)

logger = DevSynthLogger(__name__)


@dataclass(frozen=True)
class ParsedDialecticalArgument:
    """Structured representation of a dialectical argument exchange."""

    position: str
    content: str
    counterargument: str = ""


@dataclass(frozen=True)
class ChatHistoryEntry:
    """Lightweight record of a chat message used when building prompts."""

    speaker_label: str
    content: str


@dataclass(frozen=True)
class RecommendationEntry:
    """Container for parsed recommendation text."""

    text: str


def _arguments_to_primitives(
    arguments: Sequence[ParsedDialecticalArgument],
) -> list[dict[str, str]]:
    """Convert parsed argument dataclasses into repository-compatible payloads."""

    return [
        {
            "position": argument.position,
            "content": argument.content,
            "counterargument": argument.counterargument,
        }
        for argument in arguments
    ]


def _recommendations_to_primitives(
    recommendations: Sequence[RecommendationEntry],
) -> list[str]:
    """Convert recommendation entries into their textual representations."""

    return [entry.text for entry in recommendations]


class ConsensusError(BaseConsensusError):
    """Lightweight consensus error used by the requirement reasoner."""

    def __init__(self, message: str):  # pragma: no cover - simple wrapper
        Exception.__init__(self, message)


class DialecticalReasonerService(DialecticalReasonerPort):
    """
    Service for dialectical reasoning about requirement changes.
    """

    def __init__(
        self,
        requirement_repository: RequirementRepositoryPort,
        reasoning_repository: DialecticalReasoningRepositoryPort,
        impact_repository: ImpactAssessmentRepositoryPort,
        chat_repository: ChatRepositoryPort,
        notification_service: NotificationPort,
        llm_service: LLMPort,
        memory_manager: object | None = None,
    ):
        """
        Initialize the dialectical reasoner service.

        Args:
            requirement_repository: Repository for requirements.
            reasoning_repository: Repository for dialectical reasoning.
            impact_repository: Repository for impact assessments.
            chat_repository: Repository for chat sessions and messages.
            notification_service: Service for sending notifications.
            llm_service: Service for language model interactions.
        """
        self.requirement_repository = requirement_repository
        self.reasoning_repository = reasoning_repository
        self.impact_repository = impact_repository
        self.chat_repository = chat_repository
        self.notification_service = notification_service
        self.llm_service = llm_service
        self.memory_manager = memory_manager
        # Hooks mirror the WSDETeam's dialectical hooks, allowing external
        # collaborators (e.g. a WSDETeam instance) to observe evaluation
        # results.  Each hook receives the ``DialecticalReasoning`` instance and
        # a boolean indicating whether consensus was reached.
        self.evaluation_hooks: list[Callable[[DialecticalReasoning, bool], None]] = []

    # ------------------------------------------------------------------
    # Hook registration
    # ------------------------------------------------------------------
    def register_evaluation_hook(
        self, hook: Callable[[DialecticalReasoning, bool], None]
    ) -> None:
        """Register a callback to run after evaluating a change.

        The signature mirrors ``WSDETeam.register_dialectical_hook`` so team
        components can cross-reference requirement evaluations. Hooks must
        accept ``(reasoning, consensus)`` and should not raise. Any exception
        raised by a hook will later be logged and suppressed.
        """

        if not callable(hook):
            raise TypeError("hook must be callable")
        if not hasattr(self, "evaluation_hooks"):
            self.evaluation_hooks = []
        self.evaluation_hooks.append(hook)

    def _run_evaluation_hooks(
        self, reasoning: DialecticalReasoning, consensus: bool
    ) -> None:
        """Execute registered evaluation hooks.

        Hooks are best-effort; any exception is logged and suppressed so that
        evaluation proceeds unaffected.
        """

        for hook in getattr(self, "evaluation_hooks", []):
            try:
                hook(reasoning, consensus)
            except Exception:  # pragma: no cover - defensive
                logger.warning(
                    "Evaluation hook failed",  # pragma: no cover - log path
                    extra={"event": "evaluation_hook_failed"},
                    exc_info=True,
                )

    def evaluate_change(
        self,
        change: RequirementChange,
        edrr_phase: EDRRPhase = EDRRPhase.REFINE,
    ) -> DialecticalReasoning:
        """
        Evaluate a requirement change using dialectical reasoning.

        Args:
            change: The requirement change to evaluate.
            edrr_phase: The EDRR phase context for memory storage.

        Returns:
            The dialectical reasoning result.
        """
        logger.info(
            "Evaluating change",
            extra={"change_id": str(change.id), "event": "evaluation_start"},
        )
        # Check if reasoning already exists for this change
        existing_reasoning = self.reasoning_repository.get_reasoning_for_change(
            change.id
        )
        if existing_reasoning:
            return existing_reasoning

        # Create a new dialectical reasoning
        reasoning = DialecticalReasoning(
            change_id=change.id, created_by=change.created_by
        )

        # Generate thesis based on the change
        reasoning.thesis = self._generate_thesis(change)

        # Generate antithesis
        reasoning.antithesis = self._generate_antithesis(change)

        # Generate arguments
        argument_entries = self._generate_arguments(
            change, reasoning.thesis, reasoning.antithesis
        )
        reasoning.arguments = _arguments_to_primitives(argument_entries)

        # Generate synthesis
        reasoning.synthesis = self._generate_synthesis(change, argument_entries)

        # Generate conclusion and recommendation
        reasoning.conclusion, reasoning.recommendation = (
            self._generate_conclusion_and_recommendation(change, reasoning.synthesis)
        )
        # Determine consensus before persisting
        try:
            consensus_reached = self._evaluate_consensus(reasoning)
        except ConsensusError as exc:
            self._run_evaluation_hooks(reasoning, False)
            logger.error(
                "Consensus evaluation failed",  # pragma: no cover - log path
                extra={
                    "change_id": str(change.id),
                    "error": str(exc),
                    "event": "consensus_check_error",
                },
            )
            self._store_reasoning_in_memory(reasoning, edrr_phase=EDRRPhase.RETROSPECT)
            raise

        self._run_evaluation_hooks(reasoning, consensus_reached)
        if not consensus_reached:
            logger.error(
                "Consensus not reached for change",  # pragma: no cover - log path
                extra={"change_id": str(change.id), "event": "consensus_failed"},
            )
            self._store_reasoning_in_memory(reasoning, edrr_phase=EDRRPhase.RETROSPECT)
            raise ConsensusError("Consensus not reached")

        logger.info(
            "Consensus reached for change",
            extra={"change_id": str(change.id), "event": "consensus_reached"},
        )

        # Save and persist the reasoning
        saved = self.reasoning_repository.save_reasoning(reasoning)
        phase_to_use = edrr_phase
        try:
            # If default REFINE is provided but change type suggests another phase,
            # map it to align with EDRR. This keeps backward compatibility while
            # improving linkage quality.
            from devsynth.domain.models.requirement import (  # local import to avoid cycles
                ChangeType,
            )

            if edrr_phase is EDRRPhase.REFINE:
                if getattr(change, "change_type", None) == ChangeType.ADD:
                    phase_to_use = EDRRPhase.EXPAND
                elif getattr(change, "change_type", None) == ChangeType.REMOVE:
                    phase_to_use = EDRRPhase.RETROSPECT
        except Exception:
            phase_to_use = edrr_phase
        self._store_reasoning_in_memory(saved, edrr_phase=phase_to_use)
        return saved

    def process_message(
        self, session_id: UUID, message: str, user_id: str
    ) -> ChatMessage:
        """
        Process a message in a dialectical reasoning chat session.

        Args:
            session_id: The ID of the chat session.
            message: The message content.
            user_id: The ID of the user sending the message.

        Returns:
            The response message.
        """
        # Get the session
        session = self.chat_repository.get_session(session_id)
        if not session:
            raise ValueError(f"Chat session with ID {session_id} not found")

        # Add the user message to the session
        user_message = session.add_message(user_id, message)
        self.chat_repository.save_message(user_message)

        # Generate a response
        response_content = self._generate_response(session, message)

        # Add the response to the session
        response_message = session.add_message("system", response_content)
        self.chat_repository.save_message(response_message)

        # Save the updated session
        self.chat_repository.save_session(session)

        return response_message

    def create_session(
        self, user_id: str, change_id: UUID | None = None
    ) -> ChatSession:
        """
        Create a new dialectical reasoning chat session.

        Args:
            user_id: The ID of the user.
            change_id: The ID of the change to discuss, if any.

        Returns:
            The created chat session.
        """
        # Create a new session
        session = ChatSession(user_id=user_id, change_id=change_id)

        # If a change ID is provided, get the reasoning for that change
        if change_id:
            reasoning = self.reasoning_repository.get_reasoning_for_change(change_id)
            if reasoning:
                session.reasoning_id = reasoning.id

                # Add a welcome message with context about the change
                welcome_message = self._generate_welcome_message(reasoning)
                session.add_message("system", welcome_message)
        else:
            # Add a generic welcome message
            session.add_message(
                "system",
                "Welcome to the requirements dialectical reasoning system. "
                "How can I assist you with requirements management today?",
            )

        # Save and return the session
        return self.chat_repository.save_session(session)

    def assess_impact(
        self,
        change: RequirementChange,
        edrr_phase: EDRRPhase = EDRRPhase.REFINE,
    ) -> ImpactAssessment:
        """
        Assess the impact of a requirement change.

        Args:
            change: The requirement change to assess.
            edrr_phase: The EDRR phase context for memory storage.

        Returns:
            The impact assessment.
        """
        # Check if an impact assessment already exists for this change
        existing_assessment = self.impact_repository.get_impact_assessment_for_change(
            change.id
        )
        if existing_assessment:
            return existing_assessment

        # Create a new impact assessment
        assessment = ImpactAssessment(change_id=change.id, created_by=change.created_by)

        # Identify affected requirements
        assessment.affected_requirements = self._identify_affected_requirements(change)

        # Identify affected components
        assessment.affected_components = self._identify_affected_components(change)

        # Assess risk level
        assessment.risk_level = self._assess_risk_level(
            change, assessment.affected_requirements
        )

        # Estimate effort
        assessment.estimated_effort = self._estimate_effort(
            change, assessment.affected_requirements, assessment.affected_components
        )

        # Generate analysis
        assessment.analysis = self._generate_impact_analysis(
            change, assessment.affected_requirements, assessment.affected_components
        )

        # Generate recommendations
        recommendation_entries = self._generate_impact_recommendations(
            change, assessment.analysis, assessment.risk_level
        )
        assessment.recommendations = _recommendations_to_primitives(
            recommendation_entries
        )

        # Save and return the assessment
        saved_assessment = self.impact_repository.save_impact_assessment(assessment)

        # Persist impact assessment with EDRR phase context
        phase_to_use = edrr_phase
        try:
            from devsynth.domain.models.requirement import (  # local import to avoid cycles
                ChangeType,
            )

            if edrr_phase is EDRRPhase.REFINE:
                if getattr(change, "change_type", None) == ChangeType.ADD:
                    phase_to_use = EDRRPhase.EXPAND
                elif getattr(change, "change_type", None) == ChangeType.REMOVE:
                    phase_to_use = EDRRPhase.RETROSPECT
        except Exception:
            phase_to_use = edrr_phase

        # Send notification with structured payload
        impact_payload = ImpactNotificationPayload(
            assessment=saved_assessment,
            edrr_phase=phase_to_use,
        )
        self.notification_service.notify_impact_assessment_completed(impact_payload)

        self._store_impact_in_memory(saved_assessment, edrr_phase=phase_to_use)

        return saved_assessment

    def _store_reasoning_in_memory(
        self,
        reasoning: DialecticalReasoning,
        edrr_phase: EDRRPhase = EDRRPhase.REFINE,
    ) -> None:
        """Persist dialectical reasoning to the memory manager if available.

        In addition to storing the full reasoning payload, this method now
        stores a lightweight RELATIONSHIP record linking the requirement change
        to the generated reasoning, tagged with the EDRR phase. This explicit
        link enables BDD validation that requirement changes are associated with
        EDRR outcomes.
        """
        manager = getattr(self, "memory_manager", None)
        if manager is None:
            return
        try:
            # Store an explicit relationship link: requirement change -> reasoning
            relationship_payload = {
                "type": "requirement_to_reasoning",
                "change_id": str(reasoning.change_id),
                "reasoning_id": str(reasoning.id),
            }
            phase_value = edrr_phase.value
            manager.store_with_edrr_phase(
                relationship_payload,
                memory_type=MemoryType.RELATIONSHIP,
                edrr_phase=phase_value,
                metadata={
                    "change_id": str(reasoning.change_id),
                    "link": "requirement->reasoning",
                },
            )
            # Store the full reasoning record
            manager.store_with_edrr_phase(
                asdict(reasoning),
                memory_type=MemoryType.DIALECTICAL_REASONING,
                edrr_phase=phase_value,
                metadata={"change_id": str(reasoning.change_id)},
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to persist dialectical reasoning in memory",  # pragma: no cover - log path
                extra={
                    "change_id": str(reasoning.change_id),
                    "event": "reasoning_memory_persist_failed",
                },
                exc_info=True,
            )

    def _store_impact_in_memory(
        self,
        assessment: ImpactAssessment,
        edrr_phase: EDRRPhase = EDRRPhase.REFINE,
    ) -> None:
        """Persist impact assessment to the memory manager if available."""
        manager = getattr(self, "memory_manager", None)
        if manager is None:
            return
        try:
            manager.store_with_edrr_phase(
                asdict(assessment),
                memory_type=MemoryType.DOCUMENTATION,
                edrr_phase=edrr_phase.value,
                metadata={"change_id": str(assessment.change_id)},
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to persist impact assessment in memory",  # pragma: no cover - log path
                extra={
                    "change_id": str(assessment.change_id),
                    "event": "impact_memory_persist_failed",
                },
                exc_info=True,
            )

    def _evaluate_consensus(self, reasoning: DialecticalReasoning) -> bool:
        """Use the LLM to determine if consensus was achieved."""
        prompt = (
            "Determine if the following reasoning reaches consensus. "
            "Respond with 'yes' or 'no'.\n"
            f"Thesis: {reasoning.thesis}\n"
            f"Antithesis: {reasoning.antithesis}\n"
            f"Synthesis: {reasoning.synthesis}\n"
            f"Conclusion: {reasoning.conclusion}\n"
            f"Recommendation: {reasoning.recommendation}\n"
        )
        try:
            response = self.llm_service.query(prompt)
        except Exception as exc:  # pragma: no cover - defensive
            raise ConsensusError(f"Consensus check failed: {exc}") from exc

        if not isinstance(response, str):
            raise ConsensusError("Consensus check returned non-textual response")

        normalized = response.strip().lower()
        if normalized.startswith("yes"):
            return True
        if normalized.startswith("no"):
            return False

        logger.error(
            "Unexpected consensus response",  # pragma: no cover - log path
            extra={"response": response, "event": "consensus_unexpected_response"},
        )
        raise ConsensusError(f"Invalid consensus response: {response}")

    def _generate_thesis(self, change: RequirementChange) -> str:
        """
        Generate a thesis statement for a requirement change.

        Args:
            change: The requirement change.

        Returns:
            The thesis statement.
        """
        prompt = self._create_thesis_prompt(change)
        return self.llm_service.query(prompt).strip()

    def _generate_antithesis(self, change: RequirementChange) -> str:
        """
        Generate an antithesis statement for a requirement change.

        Args:
            change: The requirement change.

        Returns:
            The antithesis statement.
        """
        prompt = self._create_antithesis_prompt(change)
        return self.llm_service.query(prompt).strip()

    def _generate_arguments(
        self, change: RequirementChange, thesis: str, antithesis: str
    ) -> list[ParsedDialecticalArgument]:
        """
        Generate arguments for and against a requirement change.

        Args:
            change: The requirement change.
            thesis: The thesis statement.
            antithesis: The antithesis statement.

        Returns:
            A list of arguments.
        """
        prompt = self._create_arguments_prompt(change, thesis, antithesis)
        arguments_text: str = self.llm_service.query(prompt).strip()

        # Parse the arguments and their counterarguments into a structured format
        arguments: list[ParsedDialecticalArgument] = []
        current_position: str = ""
        current_content: str = ""
        current_counterargument: str = ""
        has_position: bool = False
        has_content: bool = False

        def _flush_current() -> None:
            nonlocal current_position, current_content, current_counterargument
            nonlocal has_position, has_content
            if has_position and has_content:
                arguments.append(
                    ParsedDialecticalArgument(
                        position=current_position,
                        content=current_content,
                        counterargument=current_counterargument,
                    )
                )
            current_position = ""
            current_content = ""
            current_counterargument = ""
            has_position = False
            has_content = False

        for line in arguments_text.split("\n"):
            normalized = line.strip()
            if not normalized:
                continue

            if normalized.startswith("Argument "):
                _flush_current()
                continue

            if ":" not in normalized:
                continue

            key, value = normalized.split(":", 1)
            key = key.strip().lower()
            cleaned_value = value.strip()

            if key == "position":
                current_position = cleaned_value
                has_position = True
            elif key in ("content", "argument"):
                current_content = cleaned_value
                has_content = True
            elif key == "counterargument":
                current_counterargument = cleaned_value

        _flush_current()

        # Deterministic ordering (can be disabled with env flag)
        if os.getenv("DEVSYNTH_DETERMINISTIC_REASONING", "1").lower() not in (
            "0",
            "false",
            "no",
        ):  # pragma: no cover - env branch

            def _pos_rank(position: str) -> int:
                p = position.lower()
                # Prefer supporting positions first for stability
                if p.startswith("for") or p.startswith("thesis"):
                    return 0
                return 1

            arguments = sorted(
                arguments,
                key=lambda a: (
                    _pos_rank(a.position),
                    a.content.lower(),
                    a.counterargument.lower(),
                ),
            )

        return arguments

    def _generate_synthesis(
        self,
        change: RequirementChange,
        arguments: Sequence[ParsedDialecticalArgument],
    ) -> str:
        """
        Generate a synthesis based on the arguments.

        Args:
            change: The requirement change.
            arguments: The arguments for and against the change.

        Returns:
            The synthesis.
        """
        prompt = self._create_synthesis_prompt(change, arguments)
        return self.llm_service.query(prompt).strip()

    def _generate_conclusion_and_recommendation(
        self, change: RequirementChange, synthesis: str
    ) -> tuple[str, str]:
        """
        Generate a conclusion and recommendation based on the synthesis.

        Args:
            change: The requirement change.
            synthesis: The synthesis of arguments.

        Returns:
            A tuple containing the conclusion and recommendation.
        """
        prompt = self._create_conclusion_prompt(change, synthesis)
        response = self.llm_service.query(prompt).strip()

        # Split the response into conclusion and recommendation
        parts = response.split("Recommendation:", 1)
        conclusion = parts[0].replace("Conclusion:", "").strip()
        recommendation = parts[1].strip() if len(parts) > 1 else ""

        return conclusion, recommendation

    def _generate_response(self, session: ChatSession, message: str) -> str:
        """
        Generate a response to a user message in a chat session.

        Args:
            session: The chat session.
            message: The user message.

        Returns:
            The response message.
        """
        # Get the change and reasoning if available
        change = None
        reasoning = None

        if session.change_id:
            # This is a session about a specific change
            change_id = session.change_id
            get_change = getattr(self.requirement_repository, "get_change", None)
            if callable(get_change):
                try:
                    change = get_change(change_id)
                except Exception:
                    change = None

        if session.reasoning_id:
            # This session has an associated reasoning
            reasoning = self.reasoning_repository.get_reasoning(session.reasoning_id)

        # Create a prompt with the chat history and context
        prompt = self._create_chat_response_prompt(session, message, change, reasoning)

        # Generate a response
        return self.llm_service.query(prompt).strip()

    def _collect_chat_history_entries(
        self, session: ChatSession
    ) -> list[ChatHistoryEntry]:
        """Return the most recent chat messages formatted for prompt injection."""

        recent_messages: list[ChatMessage] = session.messages[-5:]
        history: list[ChatHistoryEntry] = []
        for message in recent_messages:
            label = "User" if message.sender == session.user_id else "Assistant"
            history.append(
                ChatHistoryEntry(speaker_label=label, content=message.content)
            )
        return history

    def _generate_welcome_message(self, reasoning: DialecticalReasoning) -> str:
        """
        Generate a welcome message for a chat session with context about the reasoning.

        Args:
            reasoning: The dialectical reasoning.

        Returns:
            The welcome message.
        """
        # Get the change
        change = None
        if reasoning.change_id:
            get_change = getattr(self.requirement_repository, "get_change", None)
            if callable(get_change):
                try:
                    change = get_change(reasoning.change_id)
                except Exception:
                    change = None

        # Create a prompt for the welcome message
        prompt = self._create_welcome_message_prompt(reasoning, change)

        # Generate the welcome message
        return self.llm_service.query(prompt).strip()

    def _identify_affected_requirements(self, change: RequirementChange) -> list[UUID]:
        """
        Identify requirements affected by a change.

        Args:
            change: The requirement change.

        Returns:
            A list of affected requirement IDs (deterministic order).
        """
        affected_requirements: list[UUID] = []

        # If this is a modification or removal, the requirement itself is affected
        if change.requirement_id:
            affected_requirements.append(change.requirement_id)

        # Get all requirements
        all_requirements: list[Requirement] = (
            self.requirement_repository.get_all_requirements()
        )

        # Check for dependencies
        for req in all_requirements:
            # If the requirement depends on the changed requirement, it's affected
            if change.requirement_id and change.requirement_id in req.dependencies:
                affected_requirements.append(req.id)

        # Unique and deterministic
        unique = {str(r): r for r in affected_requirements}
        return [unique[k] for k in sorted(unique.keys())]

    def _identify_affected_components(self, change: RequirementChange) -> list[str]:
        """
        Identify components affected by a change.

        Args:
            change: The requirement change.

        Returns:
            A list of affected component names (deterministic order).
        """
        # For now, use a simple approach based on requirement metadata
        affected_components: list[str] = []

        if change.requirement_id:
            requirement = self.requirement_repository.get_requirement(
                change.requirement_id
            )
            if requirement and "component" in requirement.metadata:
                affected_components.append(requirement.metadata["component"])

        if change.new_state and "component" in change.new_state.metadata:
            affected_components.append(change.new_state.metadata["component"])

        # Unique and deterministic
        return sorted(set(affected_components))

    def _assess_risk_level(
        self, change: RequirementChange, affected_requirements: list[UUID]
    ) -> str:
        """
        Assess the risk level of a change.

        Args:
            change: The requirement change.
            affected_requirements: The affected requirements.

        Returns:
            The risk level.
        """
        # Simple risk assessment based on number of affected requirements and priority
        if not affected_requirements:
            return "low"

        # Get the requirement
        requirement = None
        if change.requirement_id:
            requirement = self.requirement_repository.get_requirement(
                change.requirement_id
            )

        # High priority requirement changes are higher risk
        if requirement and requirement.priority.value in ["high", "critical"]:
            if len(affected_requirements) > 3:
                return "critical"
            elif len(affected_requirements) > 1:
                return "high"
            else:
                return "medium"
        else:
            if len(affected_requirements) > 5:
                return "high"
            elif len(affected_requirements) > 2:
                return "medium"
            else:
                return "low"

    def _estimate_effort(
        self,
        change: RequirementChange,
        affected_requirements: list[UUID],
        affected_components: list[str],
    ) -> str:
        """
        Estimate the effort required for a change.

        Args:
            change: The requirement change.
            affected_requirements: The affected requirements.
            affected_components: The affected components.

        Returns:
            The estimated effort.
        """
        # Simple effort estimation based on number of affected requirements and components
        total_affected = len(affected_requirements) + len(affected_components)

        if total_affected > 8:
            return "very high"
        elif total_affected > 5:
            return "high"
        elif total_affected > 2:
            return "medium"
        else:
            return "low"

    def _generate_impact_analysis(
        self,
        change: RequirementChange,
        affected_requirements: list[UUID],
        affected_components: list[str],
    ) -> str:
        """
        Generate an impact analysis for a change.

        Args:
            change: The requirement change.
            affected_requirements: The affected requirements.
            affected_components: The affected components.

        Returns:
            The impact analysis.
        """
        # Get the affected requirements
        requirements: list[Requirement] = []
        for req_id in affected_requirements:
            req = self.requirement_repository.get_requirement(req_id)
            if req:
                requirements.append(req)

        # Create a prompt for the impact analysis
        prompt = self._create_impact_analysis_prompt(
            change, requirements, affected_components
        )

        # Generate the impact analysis
        return self.llm_service.query(prompt).strip()

    def _generate_impact_recommendations(
        self, change: RequirementChange, analysis: str, risk_level: str
    ) -> list[RecommendationEntry]:
        """
        Generate recommendations based on the impact analysis.

        Args:
            change: The requirement change.
            analysis: The impact analysis.
            risk_level: The risk level.

        Returns:
            A list of recommendations.
        """
        # Create a prompt for the recommendations
        prompt = self._create_impact_recommendations_prompt(
            change, analysis, risk_level
        )

        # Generate the recommendations
        recommendations_text: str = self.llm_service.query(prompt).strip()

        # Parse the recommendations
        recommendations: list[RecommendationEntry] = []
        for raw_line in recommendations_text.split("\n"):
            line = raw_line.strip()
            if line.startswith("- ") or line.startswith("* "):
                recommendations.append(RecommendationEntry(text=line[2:]))
            elif (
                line.startswith("1. ")
                or line.startswith("2. ")
                or line.startswith("3. ")
            ):
                recommendations.append(RecommendationEntry(text=line[3:]))

        return recommendations

    def _create_thesis_prompt(self, change: RequirementChange) -> str:
        """
        Create a prompt for generating a thesis statement.

        Args:
            change: The requirement change.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst evaluating a proposed change to a requirement. "
            "Please generate a thesis statement that argues in favor of the proposed change. "
            "The thesis should be concise, clear, and focused on the benefits of the change. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"
        prompt += "Thesis statement:"

        return prompt

    def _create_antithesis_prompt(self, change: RequirementChange) -> str:
        """
        Create a prompt for generating an antithesis statement.

        Args:
            change: The requirement change.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst evaluating a proposed change to a requirement. "
            "Please generate an antithesis statement that argues against the proposed change. "
            "The antithesis should be concise, clear, and focused on the potential drawbacks or risks of the change. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"
        prompt += "Antithesis statement:"

        return prompt

    def _create_arguments_prompt(
        self, change: RequirementChange, thesis: str, antithesis: str
    ) -> str:
        """
        Create a prompt for generating arguments.

        Args:
            change: The requirement change.
            thesis: The thesis statement.
            antithesis: The antithesis statement.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst evaluating a proposed change to a requirement. "
            "Please generate a list of arguments for and against the proposed change. "
            "For each argument, specify whether it supports the thesis or antithesis, provide a clear explanation, "
            "and then offer a counterargument that challenges the original point. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"
        prompt += f"Thesis: {thesis}\n\n"
        prompt += f"Antithesis: {antithesis}\n\n"
        prompt += (
            "Please generate at least 3 arguments for the thesis and 3 arguments for the antithesis. "
            "Format each argument and counterargument cycle as follows:\n\n"
            "Argument 1:\n"
            "Position: [Thesis/Antithesis]\n"
            "Content: [Argument content]\n"
            "Counterargument: [Counterargument content]\n\n"
            "Argument 2:\n"
            "Position: [Thesis/Antithesis]\n"
            "Content: [Argument content]\n"
            "Counterargument: [Counterargument content]\n\n"
            "And so on."
        )

        return prompt

    def _create_synthesis_prompt(
        self,
        change: RequirementChange,
        arguments: Sequence[ParsedDialecticalArgument],
    ) -> str:
        """
        Create a prompt for generating a synthesis.

        Args:
            change: The requirement change.
            arguments: The arguments for and against the change.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst evaluating a proposed change to a requirement. "
            "Please generate a synthesis that reconciles the arguments for and against the proposed change. "
            "The synthesis should acknowledge the validity of both perspectives and propose a balanced view or compromise. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"
        prompt += "Arguments:\n"

        for i, arg in enumerate(arguments, 1):
            prompt += f"Argument {i}:\n"
            prompt += f"Position: {arg.position}\n"
            prompt += f"Content: {arg.content}\n\n"

        prompt += "Synthesis:"

        return prompt

    def _create_conclusion_prompt(
        self, change: RequirementChange, synthesis: str
    ) -> str:
        """
        Create a prompt for generating a conclusion and recommendation.

        Args:
            change: The requirement change.
            synthesis: The synthesis of arguments.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst evaluating a proposed change to a requirement. "
            "Based on the synthesis of arguments, please generate a conclusion and recommendation. "
            "The conclusion should summarize the key points and the recommendation should provide clear guidance on whether to approve, reject, or modify the proposed change. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"
        prompt += f"Synthesis: {synthesis}\n\n"
        prompt += (
            "Please provide your conclusion and recommendation in the following format:\n\n"
            "Conclusion: [Your conclusion here]\n\n"
            "Recommendation: [Your recommendation here]"
        )

        return prompt

    def _create_chat_response_prompt(
        self,
        session: ChatSession,
        message: str,
        change: RequirementChange | None = None,
        reasoning: DialecticalReasoning | None = None,
    ) -> str:
        """
        Create a prompt for generating a chat response.

        Args:
            session: The chat session.
            message: The user message.
            change: The requirement change, if any.
            reasoning: The dialectical reasoning, if any.

        Returns:
            The prompt.
        """
        prompt = (
            "You are an AI assistant specializing in requirements management and dialectical reasoning. "
            "You are having a conversation with a user about requirements management. "
            "Please provide a helpful, informative, and conversational response to the user's message. "
            "\n\nChat history:\n"
        )

        # Add the chat history
        for entry in self._collect_chat_history_entries(session):
            prompt += f"{entry.speaker_label}: {entry.content}\n"

        # Add context about the change and reasoning if available
        if change:
            prompt += "\nContext - Requirement Change:\n"
            if change.change_type.value == "add":
                prompt += f"Add a new requirement: {change.new_state.title}\n"
                prompt += f"Description: {change.new_state.description}\n"
            elif change.change_type.value == "remove":
                prompt += f"Remove requirement: {change.previous_state.title}\n"
                prompt += f"Description: {change.previous_state.description}\n"
            elif change.change_type.value == "modify":
                prompt += f"Modify requirement from:\n"
                prompt += f"Title: {change.previous_state.title}\n"
                prompt += f"Description: {change.previous_state.description}\n\n"
                prompt += f"To:\n"
                prompt += f"Title: {change.new_state.title}\n"
                prompt += f"Description: {change.new_state.description}\n"

            prompt += f"Reason for change: {change.reason}\n"

        if reasoning:
            prompt += "\nContext - Dialectical Reasoning:\n"
            prompt += f"Thesis: {reasoning.thesis}\n"
            prompt += f"Antithesis: {reasoning.antithesis}\n"
            prompt += f"Synthesis: {reasoning.synthesis}\n"
            prompt += f"Conclusion: {reasoning.conclusion}\n"
            prompt += f"Recommendation: {reasoning.recommendation}\n"

        prompt += f"\nUser's latest message: {message}\n\n"
        prompt += "Your response:"

        return prompt

    def _create_welcome_message_prompt(
        self,
        reasoning: DialecticalReasoning,
        change: RequirementChange | None = None,
    ) -> str:
        """
        Create a prompt for generating a welcome message.

        Args:
            reasoning: The dialectical reasoning.
            change: The requirement change, if any.

        Returns:
            The prompt.
        """
        prompt = (
            "You are an AI assistant specializing in requirements management and dialectical reasoning. "
            "Please generate a welcome message for a user starting a chat session about a requirement change. "
            "The welcome message should introduce the dialectical reasoning system, provide context about the requirement change, "
            "and invite the user to discuss the change. "
            "\n\nDialectical Reasoning:\n"
        )

        prompt += f"Thesis: {reasoning.thesis}\n"
        prompt += f"Antithesis: {reasoning.antithesis}\n"
        prompt += f"Synthesis: {reasoning.synthesis}\n"
        prompt += f"Conclusion: {reasoning.conclusion}\n"
        prompt += f"Recommendation: {reasoning.recommendation}\n\n"

        if change:
            prompt += "Requirement Change:\n"
            if change.change_type.value == "add":
                prompt += f"Add a new requirement: {change.new_state.title}\n"
                prompt += f"Description: {change.new_state.description}\n"
            elif change.change_type.value == "remove":
                prompt += f"Remove requirement: {change.previous_state.title}\n"
                prompt += f"Description: {change.previous_state.description}\n"
            elif change.change_type.value == "modify":
                prompt += f"Modify requirement from:\n"
                prompt += f"Title: {change.previous_state.title}\n"
                prompt += f"Description: {change.previous_state.description}\n\n"
                prompt += f"To:\n"
                prompt += f"Title: {change.new_state.title}\n"
                prompt += f"Description: {change.new_state.description}\n"

            prompt += f"Reason for change: {change.reason}\n"

        prompt += "\nWelcome message:"

        return prompt

    def _create_impact_analysis_prompt(
        self,
        change: RequirementChange,
        affected_requirements: list[Requirement],
        affected_components: list[str],
    ) -> str:
        """
        Create a prompt for generating an impact analysis.

        Args:
            change: The requirement change.
            affected_requirements: The affected requirements.
            affected_components: The affected components.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst assessing the impact of a proposed change to a requirement. "
            "Please generate a comprehensive impact analysis that describes how the change will affect other requirements and components. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"

        prompt += "Affected requirements:\n"
        for req in affected_requirements:
            prompt += f"- {req.title}: {req.description}\n"

        prompt += "\nAffected components:\n"
        for component in affected_components:
            prompt += f"- {component}\n"

        prompt += "\nPlease provide a detailed impact analysis that covers:"
        prompt += "\n1. How the change affects each of the identified requirements"
        prompt += "\n2. How the change affects each of the identified components"
        prompt += "\n3. Potential ripple effects on the system as a whole"
        prompt += (
            "\n4. Technical challenges that might arise from implementing the change"
        )
        prompt += "\n5. Business implications of the change"

        prompt += "\n\nImpact analysis:"

        return prompt

    def _create_impact_recommendations_prompt(
        self, change: RequirementChange, analysis: str, risk_level: str
    ) -> str:
        """
        Create a prompt for generating impact recommendations.

        Args:
            change: The requirement change.
            analysis: The impact analysis.
            risk_level: The risk level.

        Returns:
            The prompt.
        """
        prompt = (
            "You are a requirements analyst providing recommendations based on an impact analysis of a proposed change. "
            "Please generate a list of actionable recommendations to address the impacts identified in the analysis. "
            "\n\nProposed change:\n"
        )

        if change.change_type.value == "add":
            prompt += f"Add a new requirement: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"
        elif change.change_type.value == "remove":
            prompt += f"Remove requirement: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n"
        elif change.change_type.value == "modify":
            prompt += f"Modify requirement from:\n"
            prompt += f"Title: {change.previous_state.title}\n"
            prompt += f"Description: {change.previous_state.description}\n\n"
            prompt += f"To:\n"
            prompt += f"Title: {change.new_state.title}\n"
            prompt += f"Description: {change.new_state.description}\n"

        prompt += f"\nReason for change: {change.reason}\n\n"
        prompt += f"Risk level: {risk_level}\n\n"
        prompt += f"Impact analysis: {analysis}\n\n"

        prompt += (
            "Please provide a list of 3-5 specific, actionable recommendations to address the impacts identified in the analysis. "
            "Each recommendation should be clear, concise, and focused on mitigating risks or maximizing benefits. "
            "Format the recommendations as a bulleted list."
        )

        prompt += "\n\nRecommendations:"

        return prompt
