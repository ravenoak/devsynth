"""
Consensus building functionality for Collaborative WSDE Team.

This module provides consensus building methods for the CollaborativeWSDETeam class,
including conflict identification, resolution synthesis, and decision tracking.

This is part of an effort to break up the monolithic wsde_team_extended.py
into smaller, more focused modules.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping as MappingABC
from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Union

from devsynth.application.edrr.edrr_phase_transitions import (
    MetricType,
    calculate_enhanced_quality_score,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.methodology.base import Phase

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from devsynth.domain.models.wsde_facade import WSDETeam

from .dto import (
    AgentOpinionRecord,
    ConflictRecord,
    ConsensusOutcome,
    SynthesisArtifact,
)


class ConsensusBuildingMixin:
    """Mixin class providing consensus building functionality."""

    def build_consensus(
        self, task: Dict[str, Any], phase: Optional[Phase] = None
    ) -> ConsensusOutcome:
        """Build consensus among team members with transactional safety."""

        stores: List[str] = []
        if hasattr(self, "memory_manager") and isinstance(
            self.memory_manager, MemoryManager
        ):
            stores = [
                s
                for s in ("lmdb", "faiss", "kuzu")
                if s in self.memory_manager.adapters
            ]

        if stores:
            with self.memory_manager.begin_transaction(stores):
                return self._build_consensus_inner(task, phase)
        return self._build_consensus_inner(task, phase)

    def _build_consensus_inner(
        self, task: Dict[str, Any], phase: Optional[Phase] = None
    ) -> ConsensusOutcome:
        """Internal implementation of consensus building."""
        if "id" not in task:
            task["id"] = str(uuid.uuid4())

        self.logger.info(
            f"Building consensus for task {task['id']}: {task.get('title', 'Untitled')}"
        )

        task_text = (
            (task.get("description", "") or "") + " " + (task.get("title", "") or "")
        )
        keywords = set(re.findall(r"\b\w+\b", task_text.lower()))

        agent_opinions = self._collect_agent_opinion_records(task, keywords=keywords)
        if not agent_opinions:
            self._generate_agent_opinions(task)
            agent_opinions = self._collect_agent_opinion_records(
                task, keywords=keywords
            )

        consensus_id = str(uuid.uuid4())
        conflicts = self._identify_conflicts(task, agent_opinions)
        conflict_count = len(conflicts)
        timestamp = datetime.now().isoformat()

        if conflicts:
            synthesis = self._generate_conflict_resolution_synthesis(
                task, conflicts, agent_opinions
            )
            outcome = ConsensusOutcome(
                consensus_id=consensus_id,
                task_id=task["id"],
                method="conflict_resolution_synthesis",
                achieved=True,
                agent_opinions=tuple(agent_opinions),
                conflicts=tuple(conflicts),
                conflicts_identified=conflict_count,
                synthesis=synthesis,
                timestamp=timestamp,
            )
        else:
            majority_opinion = self._identify_weighted_majority_opinion(
                agent_opinions, keywords
            )
            outcome = ConsensusOutcome(
                consensus_id=consensus_id,
                task_id=task["id"],
                method="majority_opinion",
                achieved=bool(agent_opinions),
                agent_opinions=tuple(agent_opinions),
                conflicts=tuple(conflicts),
                conflicts_identified=conflict_count,
                majority_opinion=majority_opinion or None,
                timestamp=timestamp,
            )

        explanation = self._generate_stakeholder_explanation(task, outcome)
        outcome = replace(outcome, stakeholder_explanation=explanation)
        self._track_decision(task, outcome)

        if (
            phase is not None
            and hasattr(self, "phase_metrics")
            and self.phase_metrics is not None
        ):
            existing = self.phase_metrics.get_phase_metrics(phase) or {}
            existing[MetricType.CONFLICTS.value] = conflict_count
            existing[MetricType.QUALITY.value] = calculate_enhanced_quality_score(
                outcome.to_dict()
            )
            self.phase_metrics.metrics[phase.name] = existing

        return outcome

    def _collect_agent_opinion_records(
        self,
        task: Mapping[str, Any],
        *,
        keywords: Optional[set[str]] = None,
    ) -> List[AgentOpinionRecord]:
        """Gather the latest opinion from each agent for the given task."""

        task_id = task.get("id")
        if task_id is None:
            return []

        records: List[AgentOpinionRecord] = []
        for agent in getattr(self, "agents", []):
            record = self._build_agent_opinion_record(
                agent,
                str(task_id),
                keywords=keywords,
            )
            if record is not None:
                records.append(record)
        return records

    def _build_agent_opinion_record(
        self,
        agent: Any,
        task_id: str,
        *,
        keywords: Optional[set[str]] = None,
    ) -> Optional[AgentOpinionRecord]:
        """Construct an :class:`AgentOpinionRecord` for an agent and task."""

        messages = self.get_messages(
            agent=agent.name,
            filters={"metadata.task_id": task_id, "type": "opinion"},
        )
        if not messages:
            return None

        latest_message = max(messages, key=self._message_timestamp_key)
        content = latest_message.get("content", {})
        opinion = content.get("opinion")
        rationale = content.get("rationale")
        timestamp = self._normalize_timestamp(latest_message.get("timestamp"))
        weight: Optional[float] = None
        if keywords is not None:
            weight = self._calculate_expertise_weight(agent, keywords)

        return AgentOpinionRecord(
            agent_id=getattr(agent, "name", None),
            opinion=opinion,
            rationale=rationale,
            timestamp=timestamp,
            weight=weight,
        )

    def _message_timestamp_key(self, message: Mapping[str, Any]) -> str:
        """Provide a deterministic key for ordering message timestamps."""

        timestamp = message.get("timestamp")
        if timestamp is None:
            return ""
        if isinstance(timestamp, (int, float)):
            return f"{float(timestamp):020.6f}"
        if hasattr(timestamp, "isoformat"):
            return timestamp.isoformat()  # type: ignore[no-any-return]
        return str(timestamp)

    def _normalize_timestamp(self, timestamp: Any) -> Optional[str]:
        """Convert message timestamps into ISO-formatted strings."""

        if timestamp is None:
            return None
        if hasattr(timestamp, "isoformat"):
            return timestamp.isoformat()
        return str(timestamp)

    def _identify_conflicts(
        self,
        task: Dict[str, Any],
        opinions: Optional[Sequence[AgentOpinionRecord]] = None,
    ) -> List[ConflictRecord]:
        """
        Identify conflicts in agent opinions for a task.

        Args:
            task: The task to identify conflicts for
            opinions: Optional pre-fetched agent opinions

        Returns:
            List of identified conflicts
        """

        if opinions is None:
            opinions = self._collect_agent_opinion_records(task)

        conflicts: List[ConflictRecord] = []
        opinion_map = {
            record.agent_id: record for record in opinions if record.agent_id
        }

        agent_names = list(opinion_map.keys())
        for i in range(len(agent_names)):
            for j in range(i + 1, len(agent_names)):
                agent1 = agent_names[i]
                agent2 = agent_names[j]

                opinion1 = opinion_map[agent1].opinion or ""
                opinion2 = opinion_map[agent2].opinion or ""

                if self._opinions_conflict(opinion1, opinion2):
                    severity_score = self._calculate_conflict_severity(
                        opinion1, opinion2
                    )
                    severity_label = "high" if severity_score > 0.7 else "medium"
                    conflicts.append(
                        ConflictRecord(
                            conflict_id=f"conflict_{len(conflicts)}_{task['id']}",
                            task_id=task.get("id"),
                            agent_a=agent1,
                            agent_b=agent2,
                            opinion_a=opinion1,
                            opinion_b=opinion2,
                            rationale_a=opinion_map[agent1].rationale,
                            rationale_b=opinion_map[agent2].rationale,
                            severity_label=severity_label,
                            severity_score=severity_score,
                        )
                    )

        return conflicts

    def _opinions_conflict(self, opinion1: str, opinion2: str) -> bool:
        """
        Determine if two opinions conflict with each other.

        Args:
            opinion1: First opinion
            opinion2: Second opinion

        Returns:
            True if opinions conflict, False otherwise
        """
        # Check for direct contradictions
        if "yes" in opinion1.lower() and "no" in opinion2.lower():
            return True
        if "no" in opinion1.lower() and "yes" in opinion2.lower():
            return True

        # Check for opposing recommendations
        if "should" in opinion1.lower() and "should not" in opinion2.lower():
            return True
        if "should not" in opinion1.lower() and "should" in opinion2.lower():
            return True

        # Check for different approaches
        approach1 = re.search(r"use ([a-zA-Z0-9_]+)", opinion1.lower())
        approach2 = re.search(r"use ([a-zA-Z0-9_]+)", opinion2.lower())

        if approach1 and approach2 and approach1.group(1) != approach2.group(1):
            return True

        # Check for semantic similarity (simplified)
        # In a real implementation, this would use embeddings or more sophisticated NLP
        words1 = set(re.findall(r"\b\w+\b", opinion1.lower()))
        words2 = set(re.findall(r"\b\w+\b", opinion2.lower()))

        # If opinions share less than 30% of words, they might conflict
        if len(words1.intersection(words2)) / max(len(words1), len(words2)) < 0.3:
            # Check if they're discussing the same topic
            topic_words = {"approach", "method", "solution", "implementation", "design"}
            if any(word in words1 for word in topic_words) and any(
                word in words2 for word in topic_words
            ):
                return True

        return False

    def _calculate_conflict_severity(self, opinion1: str, opinion2: str) -> float:
        """
        Calculate the severity of a conflict between two opinions.

        Args:
            opinion1: First opinion
            opinion2: Second opinion

        Returns:
            Severity score between 0 and 1
        """
        # Direct contradictions are high severity
        if "yes" in opinion1.lower() and "no" in opinion2.lower():
            return 0.9
        if "no" in opinion1.lower() and "yes" in opinion2.lower():
            return 0.9

        # Opposing recommendations are high severity
        if "should" in opinion1.lower() and "should not" in opinion2.lower():
            return 0.8
        if "should not" in opinion1.lower() and "should" in opinion2.lower():
            return 0.8

        # Different approaches are medium severity
        approach1 = re.search(r"use ([a-zA-Z0-9_]+)", opinion1.lower())
        approach2 = re.search(r"use ([a-zA-Z0-9_]+)", opinion2.lower())

        if approach1 and approach2 and approach1.group(1) != approach2.group(1):
            return 0.6

        # Calculate word overlap as a measure of agreement
        words1 = set(re.findall(r"\b\w+\b", opinion1.lower()))
        words2 = set(re.findall(r"\b\w+\b", opinion2.lower()))

        overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))

        # Convert overlap to severity (less overlap = higher severity)
        return 1.0 - overlap

    def _generate_conflict_resolution_synthesis(
        self,
        task: Dict[str, Any],
        conflicts: Sequence[ConflictRecord],
        agent_opinions: Sequence[AgentOpinionRecord],
    ) -> SynthesisArtifact:
        """
        Generate a synthesis that resolves conflicts in agent opinions.

        Args:
            task: The task to generate synthesis for
            conflicts: List of identified conflicts

        Returns:
            Synthesis resolving the conflicts
        """
        # Group conflicts by agent
        agent_conflicts: Dict[str, List[ConflictRecord]] = {}
        for conflict in conflicts:
            for agent_id in (conflict.agent_a, conflict.agent_b):
                if not agent_id:
                    continue
                agent_conflicts.setdefault(agent_id, []).append(conflict)

        # Calculate expertise weights for each agent
        expertise_weights: Dict[str, float] = {}
        for agent in self.agents:
            task_text = (
                (task.get("description", "") or "")
                + " "
                + (task.get("title", "") or "")
            )
            keywords = set(re.findall(r"\b\w+\b", task_text.lower()))
            expertise_weights[agent.name] = self._calculate_expertise_weight(
                agent, keywords
            )

        # Identify key points from each opinion, weighted by expertise
        key_points: List[Dict[str, Any]] = []
        opinion_map = {
            record.agent_id: record for record in agent_opinions if record.agent_id
        }

        for agent in self.agents:
            record = opinion_map.get(agent.name)
            if record is None:
                continue

            opinion = record.opinion or ""
            rationale = record.rationale or ""

            opinion_points = self._extract_key_points(opinion)
            rationale_points = self._extract_key_points(rationale)

            weight = record.weight
            if weight is None:
                weight = expertise_weights.get(agent.name, 1.0)

            for point in opinion_points + rationale_points:
                key_points.append(
                    {
                        "point": point,
                        "agent": agent.name,
                        "weight": weight,
                        "conflict_count": len(agent_conflicts.get(agent.name, [])),
                    }
                )

        # Sort key points by weight and conflict count (higher weight, lower conflict count first)
        key_points.sort(key=lambda p: (p["weight"], -p["conflict_count"]), reverse=True)

        # Generate synthesis
        synthesis_points = []
        covered_topics = set()

        for point in key_points:
            # Extract topic from point
            topic = self._extract_topic(point["point"])

            # Skip if topic already covered
            if topic in covered_topics:
                continue

            # Add point to synthesis
            synthesis_points.append(point["point"])
            covered_topics.add(topic)

        # Combine synthesis points into coherent text
        synthesis_text = " ".join(synthesis_points)

        # Generate final synthesis
        return SynthesisArtifact(
            text=synthesis_text,
            key_points=tuple(synthesis_points),
            expertise_weights=expertise_weights,
            conflict_resolution_method="weighted_expertise_synthesis",
            readability_score=self._calculate_readability_score(synthesis_text),
        )

    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text.

        Args:
            text: Text to extract key points from

        Returns:
            List of key points
        """
        # Split by sentences
        sentences = re.split(r"[.!?]+", text)

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        # Identify key sentences (simplified)
        key_sentences = []
        for sentence in sentences:
            # Check for indicators of key points
            if any(
                indicator in sentence.lower()
                for indicator in [
                    "should",
                    "must",
                    "recommend",
                    "suggest",
                    "important",
                    "critical",
                    "key",
                    "essential",
                ]
            ):
                key_sentences.append(sentence)

        # If no key sentences found, use all sentences
        if not key_sentences:
            key_sentences = sentences

        return key_sentences

    def _extract_topic(self, text: str) -> str:
        """
        Extract the main topic from text.

        Args:
            text: Text to extract topic from

        Returns:
            Extracted topic
        """
        # Simplified topic extraction
        # In a real implementation, this would use more sophisticated NLP

        # Look for noun phrases
        noun_phrase_match = re.search(r"the ([a-zA-Z0-9_]+)", text.lower())
        if noun_phrase_match:
            return noun_phrase_match.group(1)

        # Look for words after "should" or "must"
        modal_match = re.search(r"should|must ([a-zA-Z0-9_]+)", text.lower())
        if modal_match:
            return modal_match.group(1)

        # Default to first few words
        words = text.split()
        return " ".join(words[:3])

    def _identify_majority_opinion(
        self, agent_opinions: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Identify the majority opinion among agents.

        Args:
            agent_opinions: Dictionary mapping agent names to their opinions

        Returns:
            The majority opinion
        """
        # Count opinions
        opinion_counts = {}
        for agent, data in agent_opinions.items():
            opinion = data["opinion"]
            opinion_counts[opinion] = opinion_counts.get(opinion, 0) + 1

        # Find majority opinion
        majority_opinion = max(opinion_counts.items(), key=lambda x: x[1])[0]

        return majority_opinion

    def _identify_weighted_majority_opinion(
        self, agent_opinions: Sequence[AgentOpinionRecord], keywords: set[str]
    ) -> str:
        """Identify the majority opinion using expertise-based weighting.

        Args:
            agent_opinions: Agent opinion records to analyse
            keywords: Keywords extracted from the task context

        Returns:
            The opinion with the highest weighted support
        """
        # Build expertise weights for all agents
        weights = {
            agent.name: self._calculate_expertise_weight(agent, keywords)
            for agent in self.agents
        }

        # Sum weighted support for each opinion
        weighted_counts: Dict[str, float] = {}
        opinion_lookup = {
            record.agent_id: record for record in agent_opinions if record.agent_id
        }
        for agent_id, record in opinion_lookup.items():
            opinion = record.opinion
            if not opinion:
                continue
            weight = record.weight
            if weight is None:
                weight = weights.get(agent_id, 1.0)
            weighted_counts[opinion] = weighted_counts.get(opinion, 0.0) + weight

        # Determine winning opinion
        max_weight = max(weighted_counts.values()) if weighted_counts else 0
        top_opinions = [op for op, val in weighted_counts.items() if val == max_weight]

        if len(top_opinions) > 1:
            primus = getattr(self, "get_primus", lambda: None)()
            if primus and primus.name in opinion_lookup:
                primus_choice = opinion_lookup[primus.name].opinion
                if primus_choice and primus_choice in top_opinions:
                    return primus_choice
            return top_opinions[0]

        return top_opinions[0] if top_opinions else ""

    def _calculate_expertise_weight(self, agent: Any, keywords: set) -> float:
        """
        Calculate expertise weight for an agent based on task keywords.

        Args:
            agent: The agent to calculate weight for
            keywords: Set of keywords from the task

        Returns:
            Expertise weight between 0 and 1
        """
        # Get agent expertise
        expertise = []
        if hasattr(agent, "expertise"):
            expertise = agent.expertise
        elif hasattr(agent, "metadata") and "expertise" in agent.metadata:
            expertise = agent.metadata["expertise"]
        elif hasattr(agent, "get_expertise"):
            expertise = agent.get_expertise()

        # Convert expertise to set of words
        expertise_words = set()
        for exp in expertise:
            expertise_words.update(re.findall(r"\b\w+\b", exp.lower()))

        # Calculate overlap between expertise and keywords
        if not expertise_words or not keywords:
            return 0.5  # Default weight

        overlap = len(expertise_words.intersection(keywords)) / len(keywords)

        # Scale overlap to weight between 0.5 and 1.0
        weight = 0.5 + (0.5 * overlap)

        return weight

    def _track_decision(
        self, task: Dict[str, Any], consensus_result: ConsensusOutcome
    ) -> None:
        """
        Track a decision made through consensus building.

        Args:
            task: The task the decision was made for
            consensus_result: The consensus result
        """
        # Generate decision ID aligned with the consensus outcome identifier
        decision_id = (
            consensus_result.consensus_id
            or f"decision_{task['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        formatted_opinions: Dict[str, Dict[str, Any]] = {}
        for record in consensus_result.agent_opinions:
            if not record.agent_id:
                continue
            formatted_opinions[record.agent_id] = {
                "opinion": record.opinion,
                "rationale": record.rationale,
                "timestamp": record.timestamp,
                "weight": record.weight,
            }

        decision: Dict[str, Any] = {
            "id": decision_id,
            "task_id": task.get("id"),
            "task_title": task.get("title", "Untitled"),
            "task_description": task.get("description", ""),
            "consensus_method": consensus_result.method,
            "agent_opinions": formatted_opinions,
            "timestamp": datetime.now().isoformat(),
            "implemented": False,
            "implementation_details": None,
            "consensus_snapshot": consensus_result.to_dict(),
        }

        if consensus_result.synthesis is not None:
            decision["synthesis"] = consensus_result.synthesis.to_dict()

        if consensus_result.majority_opinion:
            decision["majority_opinion"] = consensus_result.majority_opinion

        if consensus_result.stakeholder_explanation:
            decision["stakeholder_explanation"] = (
                consensus_result.stakeholder_explanation
            )

        self.tracked_decisions[decision_id] = decision

        if hasattr(self, "memory_manager") and self.memory_manager is not None:
            import json

            item = MemoryItem(
                id=decision_id,
                content=json.dumps(decision),
                memory_type=MemoryType.TEAM_STATE,
                metadata={"type": "CONSENSUS_DECISION"},
            )
            try:
                if "tinydb" in self.memory_manager.adapters:
                    primary = "tinydb"
                elif "graph" in self.memory_manager.adapters:
                    primary = "graph"
                elif self.memory_manager.adapters:
                    primary = next(iter(self.memory_manager.adapters))
                else:
                    primary = None

                if primary:
                    self.memory_manager.update_item(primary, item)
                    # Also store a summary for quick retrieval
                    summary_text = self.summarize_consensus_result(consensus_result)
                    summary_item = MemoryItem(
                        id=f"{decision_id}_summary",
                        content=json.dumps(
                            {"decision_id": decision_id, "summary": summary_text}
                        ),
                        memory_type=MemoryType.TEAM_STATE,
                        metadata={"type": "CONSENSUS_SUMMARY"},
                    )
                    self.memory_manager.update_item(primary, summary_item)
                    if "faiss" in self.memory_manager.adapters:
                        try:
                            embedding = self.memory_manager._embed_text(summary_text)
                            vector = MemoryVector(
                                id=decision_id,
                                content=summary_text,
                                embedding=embedding,
                                metadata={"type": "CONSENSUS_VECTOR"},
                            )
                            self.memory_manager.adapters["faiss"].store_vector(vector)
                        except Exception:
                            pass
                    try:
                        self.memory_manager.flush_updates()
                    except Exception:
                        pass
            except Exception:
                pass

        # Log decision tracking
        self.logger.info(f"Tracked decision {decision_id} for task {task['id']}")

    def _generate_agent_opinions(self, task: Dict[str, Any]) -> None:
        """
        Generate opinions from agents for a task.

        Args:
            task: The task to generate opinions for
        """
        # For each agent, request an opinion
        for agent in self.agents:
            # Send a message to the agent requesting an opinion
            self.send_message(
                sender="system",
                recipients=[agent.name],
                message_type="opinion_request",
                subject=f"Opinion Request: {task.get('title', 'Untitled')}",
                content=task,
                metadata={"task_id": task["id"]},
            )

            # In a real implementation, we would wait for the agent to respond
            # For this example, we'll simulate a response

            # Generate a simulated opinion
            opinion = f"I think we should {['implement', 'consider', 'analyze', 'design'][hash(agent.name) % 4]} the {task.get('title', 'task')}."
            rationale = f"Based on my expertise in {agent.metadata.get('expertise', ['general'])[0]}, this approach would be most effective."

            # Send the opinion as a message
            self.send_message(
                sender=agent.name,
                recipients=["system"],
                message_type="opinion",
                subject=f"Opinion on {task.get('title', 'Untitled')}",
                content={"opinion": opinion, "rationale": rationale},
                metadata={"task_id": task["id"]},
            )

    def _calculate_readability_score(self, text: str) -> Dict[str, float]:
        """
        Calculate readability metrics for text.

        Args:
            text: Text to calculate readability for

        Returns:
            Dictionary of readability metrics
        """
        # Count sentences, words, and syllables
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = re.findall(r"\b\w+\b", text.lower())

        def count_syllables(word):
            """Count the number of syllables in a word."""
            # This is a simplified syllable counter
            word = word.lower()

            # Remove ending e
            if word.endswith("e"):
                word = word[:-1]

            # Count vowel groups
            vowels = "aeiouy"
            count = 0
            in_vowel_group = False

            for char in word:
                if char in vowels:
                    if not in_vowel_group:
                        count += 1
                        in_vowel_group = True
                else:
                    in_vowel_group = False

            # Ensure at least one syllable
            return max(1, count)

        syllables = sum(count_syllables(word) for word in words)

        # Calculate metrics
        num_sentences = len(sentences)
        num_words = len(words)

        if num_sentences == 0 or num_words == 0:
            return {
                "flesch_reading_ease": 0,
                "flesch_kincaid_grade": 0,
                "syllables_per_word": 0,
                "words_per_sentence": 0,
            }

        # Flesch Reading Ease
        flesch_reading_ease = (
            206.835
            - (1.015 * (num_words / num_sentences))
            - (84.6 * (syllables / num_words))
        )

        # Flesch-Kincaid Grade Level
        flesch_kincaid_grade = (
            (0.39 * (num_words / num_sentences))
            + (11.8 * (syllables / num_words))
            - 15.59
        )

        return {
            "flesch_reading_ease": flesch_reading_ease,
            "flesch_kincaid_grade": flesch_kincaid_grade,
            "syllables_per_word": syllables / num_words,
            "words_per_sentence": num_words / num_sentences,
        }

    def _generate_stakeholder_explanation(
        self, task: Dict[str, Any], consensus_result: ConsensusOutcome
    ) -> str:
        """
        Generate an explanation of the consensus result for stakeholders.

        Args:
            task: The task the consensus was built for
            consensus_result: The consensus result

        Returns:
            Stakeholder-friendly explanation
        """
        # Start with a summary
        explanation = f"Decision summary for '{task.get('title', 'Untitled')}': "

        method = consensus_result.method or "consensus"

        # Add method-specific explanation
        if method == "conflict_resolution_synthesis":
            # Synthesis-based consensus
            synthesis = consensus_result.synthesis
            synthesis_text = (synthesis.text if synthesis else "") or ""

            explanation += f"After analyzing different perspectives, we reached a synthesis-based decision. "
            explanation += f"The key points of our decision are: {synthesis_text} "

            # Add information about conflicts
            num_conflicts = consensus_result.conflicts_identified
            explanation += f"We identified and resolved {num_conflicts} conflicts in perspectives. "

            # Add readability information
            readability = synthesis.readability_score if synthesis else {}
            if readability:
                grade_level = readability.get("flesch_kincaid_grade", 0)
                explanation += f"This explanation is written at approximately a grade {grade_level:.1f} reading level. "
        else:
            # Majority opinion
            majority_opinion = consensus_result.majority_opinion or ""
            explanation += f"The team reached a consensus through majority agreement. "
            explanation += f"The decision is: {majority_opinion} "

            # Count supporting agents
            opinions = consensus_result.agent_opinions
            supporting_agents = sum(
                1 for record in opinions if record.opinion == majority_opinion
            )
            total_participants = len(opinions)
            explanation += f"This decision was supported by {supporting_agents} out of {total_participants} team members. "

        # Add next steps
        explanation += "Next steps: Implement the decision and monitor outcomes. "
        explanation += "If you have questions or concerns about this decision, please contact the team lead."

        return explanation

    def get_tracked_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tracked decision by ID.

        Args:
            decision_id: ID of the decision to retrieve

        Returns:
            The decision record or None if not found
        """
        return self.tracked_decisions.get(decision_id)

    def mark_decision_implemented(self, decision_id: str) -> bool:
        """
        Mark a decision as implemented.

        Args:
            decision_id: ID of the decision to mark

        Returns:
            True if successful, False if decision not found
        """
        if decision_id not in self.tracked_decisions:
            return False

        self.tracked_decisions[decision_id]["implemented"] = True
        self.tracked_decisions[decision_id][
            "implementation_timestamp"
        ] = datetime.now().isoformat()

        return True

    def add_decision_implementation_details(
        self, decision_id: str, details: Dict[str, Any]
    ) -> bool:
        """
        Add implementation details to a tracked decision.

        Args:
            decision_id: ID of the decision
            details: Implementation details

        Returns:
            True if successful, False if decision not found
        """
        if decision_id not in self.tracked_decisions:
            return False

        self.tracked_decisions[decision_id]["implementation_details"] = details

        return True

    def query_decisions(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Query tracked decisions with filters.

        Args:
            **kwargs: Filter criteria (e.g., task_id, implemented)

        Returns:
            List of matching decision records
        """
        results = []

        for decision_id, decision in self.tracked_decisions.items():
            # Check if decision matches all criteria
            matches = True
            for key, value in kwargs.items():
                if key not in decision or decision[key] != value:
                    matches = False
                    break

            if matches:
                results.append(decision)

        return results

    def has_decision_documentation(self, decision_id: str) -> bool:
        """
        Check if a decision has documentation.

        Args:
            decision_id: ID of the decision

        Returns:
            True if decision has documentation, False otherwise
        """
        if decision_id not in self.tracked_decisions:
            return False

        decision = self.tracked_decisions[decision_id]

        # Check for synthesis or majority opinion
        has_synthesis = "synthesis" in decision and decision["synthesis"].get(
            "text", ""
        )
        has_majority_opinion = (
            "majority_opinion" in decision and decision["majority_opinion"]
        )

        # Check for implementation details
        has_implementation = (
            "implementation_details" in decision and decision["implementation_details"]
        )

        return (has_synthesis or has_majority_opinion) and has_implementation

    def summarize_voting_result(self, voting_result: Dict[str, Any]) -> str:
        """Create a short human readable summary of a voting result."""

        if not voting_result:
            return "No voting result available."

        status = voting_result.get("status")
        if status == "failed":
            return voting_result.get("reason", "Voting failed")

        result = voting_result.get("result")

        # Handle tied vote summaries
        if isinstance(result, dict) and result.get("tied"):
            tied_options = ", ".join(result.get("tied_options", []))
            summary = f"Vote resulted in a tie between {tied_options}."
            tie_resolution = voting_result.get("tie_resolution")
            if tie_resolution and tie_resolution.get("winner"):
                summary += f" Tie resolved in favour of {tie_resolution['winner']}."
            self._store_voting_summary(summary, voting_result)
            return summary

        # Normal voting outcome
        winner = None
        if isinstance(result, dict):
            winner = result.get("winner")
        elif result:
            winner = result
        if not winner and isinstance(voting_result.get("selected_option"), dict):
            winner = voting_result["selected_option"].get("id")

        if winner:
            vote_counts = voting_result.get("vote_counts", {})
            count = vote_counts.get(winner, 0)
            summary = f"Option '{winner}' selected with {count} votes."
            self._store_voting_summary(summary, voting_result)
            return summary

        summary = "Voting completed."
        self._store_voting_summary(summary, voting_result)
        return summary

    def _store_voting_summary(
        self, summary: str, voting_result: Dict[str, Any]
    ) -> None:
        """Persist a voting summary to memory if available."""
        if (
            not summary
            or not hasattr(self, "memory_manager")
            or self.memory_manager is None
        ):
            return
        try:
            if "tinydb" in self.memory_manager.adapters:
                primary = "tinydb"
            elif "graph" in self.memory_manager.adapters:
                primary = "graph"
            elif self.memory_manager.adapters:
                primary = next(iter(self.memory_manager.adapters))
            else:
                primary = None
            if primary:
                item = MemoryItem(
                    id=f"voting_summary_{uuid.uuid4()}",
                    content={"summary": summary, "voting_result": voting_result},
                    memory_type=MemoryType.TEAM_STATE,
                    metadata={"type": "VOTING_SUMMARY"},
                )
                self.memory_manager.update_item(primary, item)
                try:
                    self.memory_manager.flush_updates()
                except Exception:
                    pass
        except Exception:
            pass

    def summarize_consensus_result(
        self, consensus_result: Union[ConsensusOutcome, Mapping[str, Any], None]
    ) -> str:
        """Generate a concise summary from a consensus result."""

        if not consensus_result:
            return "No consensus result available."

        if isinstance(consensus_result, MappingABC):
            try:
                consensus_result = ConsensusOutcome.from_dict(consensus_result)
            except Exception:
                method = str(consensus_result.get("method", "consensus"))
                if "synthesis" in consensus_result:
                    text = consensus_result["synthesis"].get("text", "").strip()
                    summary = (
                        f"Synthesis consensus reached: {text}"
                        if text
                        else "Synthesis consensus reached."
                    )
                elif "majority_opinion" in consensus_result:
                    summary = f"Majority opinion chosen: {consensus_result['majority_opinion']}"
                else:
                    summary = f"Consensus result: {consensus_result.get('result', '')}"
                if method:
                    summary += f" (method: {method})"
                return summary

        if not isinstance(consensus_result, ConsensusOutcome):
            return "No consensus result available."

        method = consensus_result.method or "consensus"

        if (
            consensus_result.synthesis is not None
            and (consensus_result.synthesis.text or "").strip()
        ):
            summary = (
                "Synthesis consensus reached: "
                f"{consensus_result.synthesis.text.strip()}"
            )
        elif consensus_result.synthesis is not None:
            summary = "Synthesis consensus reached."
        elif consensus_result.majority_opinion:
            summary = f"Majority opinion chosen: {consensus_result.majority_opinion}"
        else:
            summary = "Consensus result recorded."

        if method:
            summary += f" (method: {method})"

        return summary
