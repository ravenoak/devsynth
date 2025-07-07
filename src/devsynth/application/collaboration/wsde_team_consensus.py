"""
Consensus building functionality for Collaborative WSDE Team.

This module provides consensus building methods for the CollaborativeWSDETeam class,
including conflict identification, resolution synthesis, and decision tracking.

This is part of an effort to break up the monolithic wsde_team_extended.py
into smaller, more focused modules.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid
import re

from devsynth.domain.models.wsde_facade import WSDETeam


class ConsensusBuildingMixin:
    """
    Mixin class providing consensus building functionality for CollaborativeWSDETeam.

    This mixin adds methods for building consensus, identifying conflicts,
    generating conflict resolution synthesis, and tracking decisions.
    """

    def build_consensus(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build consensus among team members for a given task.

        Args:
            task: The task to build consensus for

        Returns:
            The consensus result
        """
        # Ensure task has an ID
        if "id" not in task:
            task["id"] = str(uuid.uuid4())

        # Log the consensus building
        self.logger.info(f"Building consensus for task {task['id']}: {task.get('title', 'Untitled')}")

        # Get all agents' opinions
        agent_opinions = {}
        for agent in self.agents:
            # Get messages from this agent related to the task
            messages = self.get_messages(
                agent=agent.name,
                filters={"metadata.task_id": task["id"], "type": "opinion"}
            )

            if messages:
                # Use the latest opinion
                latest_message = max(messages, key=lambda m: m["timestamp"])
                opinion = latest_message["content"].get("opinion", "")
                rationale = latest_message["content"].get("rationale", "")

                agent_opinions[agent.name] = {
                    "opinion": opinion,
                    "rationale": rationale,
                    "timestamp": latest_message["timestamp"]
                }

        # If no opinions, try to generate them
        if not agent_opinions:
            self._generate_agent_opinions(task)

            # Try again to get opinions
            for agent in self.agents:
                messages = self.get_messages(
                    agent=agent.name,
                    filters={"metadata.task_id": task["id"], "type": "opinion"}
                )

                if messages:
                    latest_message = max(messages, key=lambda m: m["timestamp"])
                    opinion = latest_message["content"].get("opinion", "")
                    rationale = latest_message["content"].get("rationale", "")

                    agent_opinions[agent.name] = {
                        "opinion": opinion,
                        "rationale": rationale,
                        "timestamp": latest_message["timestamp"]
                    }

        # Identify conflicts in opinions
        conflicts = self._identify_conflicts(task)

        # Generate consensus result
        if conflicts:
            # If there are conflicts, generate a synthesis
            synthesis = self._generate_conflict_resolution_synthesis(task, conflicts)

            consensus_result = {
                "task_id": task["id"],
                "method": "conflict_resolution_synthesis",
                "conflicts_identified": len(conflicts),
                "synthesis": synthesis,
                "agent_opinions": agent_opinions,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # If no conflicts, use majority opinion
            majority_opinion = self._identify_majority_opinion(agent_opinions)

            consensus_result = {
                "task_id": task["id"],
                "method": "majority_opinion",
                "majority_opinion": majority_opinion,
                "agent_opinions": agent_opinions,
                "timestamp": datetime.now().isoformat()
            }

        # Track the decision
        self._track_decision(task, consensus_result)

        # Generate stakeholder explanation
        explanation = self._generate_stakeholder_explanation(task, consensus_result)
        consensus_result["stakeholder_explanation"] = explanation

        return consensus_result

    def _identify_conflicts(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify conflicts in agent opinions for a task.

        Args:
            task: The task to identify conflicts for

        Returns:
            List of identified conflicts
        """
        conflicts = []

        # Get all agents' opinions
        agent_opinions = {}
        for agent in self.agents:
            # Get messages from this agent related to the task
            messages = self.get_messages(
                agent=agent.name,
                filters={"metadata.task_id": task["id"], "type": "opinion"}
            )

            if messages:
                # Use the latest opinion
                latest_message = max(messages, key=lambda m: m["timestamp"])
                opinion = latest_message["content"].get("opinion", "")
                rationale = latest_message["content"].get("rationale", "")

                agent_opinions[agent.name] = {
                    "opinion": opinion,
                    "rationale": rationale
                }

        # Compare opinions pairwise
        agent_names = list(agent_opinions.keys())
        for i in range(len(agent_names)):
            for j in range(i + 1, len(agent_names)):
                agent1 = agent_names[i]
                agent2 = agent_names[j]

                opinion1 = agent_opinions[agent1]["opinion"]
                opinion2 = agent_opinions[agent2]["opinion"]

                # Check if opinions conflict
                if self._opinions_conflict(opinion1, opinion2):
                    conflict = {
                        "id": f"conflict_{len(conflicts)}_{task['id']}",
                        "task_id": task["id"],
                        "agent1": agent1,
                        "agent2": agent2,
                        "opinion1": opinion1,
                        "opinion2": opinion2,
                        "rationale1": agent_opinions[agent1]["rationale"],
                        "rationale2": agent_opinions[agent2]["rationale"],
                        "severity": "high" if self._calculate_conflict_severity(opinion1, opinion2) > 0.7 else "medium"
                    }
                    conflicts.append(conflict)

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
        words1 = set(re.findall(r'\b\w+\b', opinion1.lower()))
        words2 = set(re.findall(r'\b\w+\b', opinion2.lower()))

        # If opinions share less than 30% of words, they might conflict
        if len(words1.intersection(words2)) / max(len(words1), len(words2)) < 0.3:
            # Check if they're discussing the same topic
            topic_words = {"approach", "method", "solution", "implementation", "design"}
            if any(word in words1 for word in topic_words) and any(word in words2 for word in topic_words):
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
        words1 = set(re.findall(r'\b\w+\b', opinion1.lower()))
        words2 = set(re.findall(r'\b\w+\b', opinion2.lower()))

        overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))

        # Convert overlap to severity (less overlap = higher severity)
        return 1.0 - overlap

    def _generate_conflict_resolution_synthesis(self, task: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a synthesis that resolves conflicts in agent opinions.

        Args:
            task: The task to generate synthesis for
            conflicts: List of identified conflicts

        Returns:
            Synthesis resolving the conflicts
        """
        # Group conflicts by agent
        agent_conflicts = {}
        for conflict in conflicts:
            agent1 = conflict["agent1"]
            agent2 = conflict["agent2"]

            if agent1 not in agent_conflicts:
                agent_conflicts[agent1] = []
            if agent2 not in agent_conflicts:
                agent_conflicts[agent2] = []

            agent_conflicts[agent1].append(conflict)
            agent_conflicts[agent2].append(conflict)

        # Calculate expertise weights for each agent
        expertise_weights = {}
        for agent in self.agents:
            # Extract keywords from task
            task_text = task.get("description", "") + " " + task.get("title", "")
            keywords = set(re.findall(r'\b\w+\b', task_text.lower()))

            # Calculate expertise weight
            expertise_weights[agent.name] = self._calculate_expertise_weight(agent, keywords)

        # Identify key points from each opinion, weighted by expertise
        key_points = []
        for agent in self.agents:
            # Get agent's opinion
            messages = self.get_messages(
                agent=agent.name,
                filters={"metadata.task_id": task["id"], "type": "opinion"}
            )

            if not messages:
                continue

            latest_message = max(messages, key=lambda m: m["timestamp"])
            opinion = latest_message["content"].get("opinion", "")
            rationale = latest_message["content"].get("rationale", "")

            # Extract key points from opinion and rationale
            opinion_points = self._extract_key_points(opinion)
            rationale_points = self._extract_key_points(rationale)

            # Weight points by expertise
            weight = expertise_weights.get(agent.name, 1.0)

            for point in opinion_points + rationale_points:
                key_points.append({
                    "point": point,
                    "agent": agent.name,
                    "weight": weight,
                    "conflict_count": len(agent_conflicts.get(agent.name, []))
                })

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
        synthesis = {
            "text": synthesis_text,
            "key_points": synthesis_points,
            "expertise_weights": expertise_weights,
            "conflict_resolution_method": "weighted_expertise_synthesis",
            "readability_score": self._calculate_readability_score(synthesis_text)
        }

        return synthesis

    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text.

        Args:
            text: Text to extract key points from

        Returns:
            List of key points
        """
        # Split by sentences
        sentences = re.split(r'[.!?]+', text)

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        # Identify key sentences (simplified)
        key_sentences = []
        for sentence in sentences:
            # Check for indicators of key points
            if any(indicator in sentence.lower() for indicator in 
                  ["should", "must", "recommend", "suggest", "important", "critical", "key", "essential"]):
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
        noun_phrase_match = re.search(r'the ([a-zA-Z0-9_]+)', text.lower())
        if noun_phrase_match:
            return noun_phrase_match.group(1)

        # Look for words after "should" or "must"
        modal_match = re.search(r'should|must ([a-zA-Z0-9_]+)', text.lower())
        if modal_match:
            return modal_match.group(1)

        # Default to first few words
        words = text.split()
        return " ".join(words[:3])

    def _identify_majority_opinion(self, agent_opinions: Dict[str, Dict[str, Any]]) -> str:
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
            expertise_words.update(re.findall(r'\b\w+\b', exp.lower()))

        # Calculate overlap between expertise and keywords
        if not expertise_words or not keywords:
            return 0.5  # Default weight

        overlap = len(expertise_words.intersection(keywords)) / len(keywords)

        # Scale overlap to weight between 0.5 and 1.0
        weight = 0.5 + (0.5 * overlap)

        return weight

    def _track_decision(self, task: Dict[str, Any], consensus_result: Dict[str, Any]) -> None:
        """
        Track a decision made through consensus building.

        Args:
            task: The task the decision was made for
            consensus_result: The consensus result
        """
        # Generate decision ID
        decision_id = f"decision_{task['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create decision record
        decision = {
            "id": decision_id,
            "task_id": task["id"],
            "task_title": task.get("title", "Untitled"),
            "task_description": task.get("description", ""),
            "consensus_method": consensus_result["method"],
            "agent_opinions": consensus_result["agent_opinions"],
            "timestamp": datetime.now().isoformat(),
            "implemented": False,
            "implementation_details": None
        }

        # Add synthesis if available
        if "synthesis" in consensus_result:
            decision["synthesis"] = consensus_result["synthesis"]

        # Add majority opinion if available
        if "majority_opinion" in consensus_result:
            decision["majority_opinion"] = consensus_result["majority_opinion"]

        # Store decision
        self.tracked_decisions[decision_id] = decision

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
                metadata={"task_id": task["id"]}
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
                content={
                    "opinion": opinion,
                    "rationale": rationale
                },
                metadata={"task_id": task["id"]}
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
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = re.findall(r'\b\w+\b', text.lower())

        def count_syllables(word):
            """Count the number of syllables in a word."""
            # This is a simplified syllable counter
            word = word.lower()

            # Remove ending e
            if word.endswith('e'):
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
                "words_per_sentence": 0
            }

        # Flesch Reading Ease
        flesch_reading_ease = 206.835 - (1.015 * (num_words / num_sentences)) - (84.6 * (syllables / num_words))

        # Flesch-Kincaid Grade Level
        flesch_kincaid_grade = (0.39 * (num_words / num_sentences)) + (11.8 * (syllables / num_words)) - 15.59

        return {
            "flesch_reading_ease": flesch_reading_ease,
            "flesch_kincaid_grade": flesch_kincaid_grade,
            "syllables_per_word": syllables / num_words,
            "words_per_sentence": num_words / num_sentences
        }

    def _generate_stakeholder_explanation(self, task: Dict[str, Any], consensus_result: Dict[str, Any]) -> str:
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

        # Add method-specific explanation
        if consensus_result["method"] == "conflict_resolution_synthesis":
            # Synthesis-based consensus
            synthesis = consensus_result.get("synthesis", {})
            synthesis_text = synthesis.get("text", "")

            explanation += f"After analyzing different perspectives, we reached a synthesis-based decision. "
            explanation += f"The key points of our decision are: {synthesis_text} "

            # Add information about conflicts
            num_conflicts = consensus_result.get("conflicts_identified", 0)
            explanation += f"We identified and resolved {num_conflicts} conflicts in perspectives. "

            # Add readability information
            readability = synthesis.get("readability_score", {})
            if readability:
                grade_level = readability.get("flesch_kincaid_grade", 0)
                explanation += f"This explanation is written at approximately a grade {grade_level:.1f} reading level. "
        else:
            # Majority opinion
            majority_opinion = consensus_result.get("majority_opinion", "")
            explanation += f"The team reached a consensus through majority agreement. "
            explanation += f"The decision is: {majority_opinion} "

            # Count supporting agents
            supporting_agents = 0
            for agent, data in consensus_result.get("agent_opinions", {}).items():
                if data.get("opinion") == majority_opinion:
                    supporting_agents += 1

            explanation += f"This decision was supported by {supporting_agents} out of {len(consensus_result.get('agent_opinions', {}))} team members. "

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
        self.tracked_decisions[decision_id]["implementation_timestamp"] = datetime.now().isoformat()

        return True

    def add_decision_implementation_details(self, decision_id: str, details: Dict[str, Any]) -> bool:
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
        has_synthesis = "synthesis" in decision and decision["synthesis"].get("text", "")
        has_majority_opinion = "majority_opinion" in decision and decision["majority_opinion"]

        # Check for implementation details
        has_implementation = "implementation_details" in decision and decision["implementation_details"]

        return (has_synthesis or has_majority_opinion) and has_implementation
