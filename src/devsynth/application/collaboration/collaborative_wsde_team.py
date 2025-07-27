"""
Collaborative WSDE Team implementation.

This module provides the CollaborativeWSDETeam class, which combines various mixins
to create a comprehensive collaborative team implementation.

This is part of an effort to break up the monolithic wsde_team_extended.py
into smaller, more focused modules.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid

from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.application.collaboration.wsde_team_task_management import (
    TaskManagementMixin,
)
from devsynth.application.collaboration.wsde_team_consensus import (
    ConsensusBuildingMixin,
)


class CollaborativeWSDETeam(TaskManagementMixin, ConsensusBuildingMixin, WSDETeam):
    """
    Collaborative Worker Self-Directed Enterprise Team.

    This class extends the base WSDETeam with enhanced collaborative capabilities
    by combining various mixins:
    - TaskManagementMixin: Provides task management functionality
    - ConsensusBuildingMixin: Provides consensus building functionality

    The CollaborativeWSDETeam supports advanced features like:
    - Collaborative decision making
    - Task delegation and progress tracking
    - Consensus building with conflict resolution
    - Decision tracking and documentation
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a new CollaborativeWSDETeam.

        Args:
            name: The name of the team
            description: Optional description of the team's purpose
        """
        super().__init__(name, description)

        # Initialize attributes for task management
        self.subtasks = {}
        self.subtask_progress = {}

        # Initialize attributes for consensus building
        self.tracked_decisions = {}

        # Initialize metrics
        self.contribution_metrics = {}
        self.role_history = []
        self.leadership_reassessments = {}
        self.transition_metrics = {}
        self.collaboration_metrics = {}

    def solve_collaboratively(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve a problem collaboratively using the team's expertise.

        This is a high-level method that orchestrates the collaborative problem-solving
        process, including task processing, consensus building, and result synthesis.

        Args:
            problem: The problem to solve

        Returns:
            The collaborative solution
        """
        # Ensure problem has an ID
        if "id" not in problem:
            problem["id"] = str(uuid.uuid4())

        # Log the collaborative problem solving
        self.logger.info(
            f"Solving problem {problem['id']} collaboratively: {problem.get('title', 'Untitled')}"
        )

        # Process the problem as a task
        processed_task = self.process_task(problem)

        # Build consensus on the approach
        consensus = self.build_consensus(processed_task)

        # Collect results from subtasks
        subtask_results = processed_task.get("results", [])

        # Generate final solution
        solution = {
            "problem_id": problem["id"],
            "title": problem.get("title", "Untitled"),
            "approach": consensus.get("method", "unknown"),
            "consensus": consensus,
            "subtask_results": subtask_results,
            "timestamp": datetime.now().isoformat(),
        }

        # If consensus was reached through synthesis, use it as the solution
        if "synthesis" in consensus:
            solution["solution"] = consensus["synthesis"].get("text", "")
            solution["key_points"] = consensus["synthesis"].get("key_points", [])
        else:
            # Otherwise, use majority opinion
            solution["solution"] = consensus.get("majority_opinion", "")

        # Add stakeholder explanation
        solution["explanation"] = consensus.get("stakeholder_explanation", "")

        # Update collaboration metrics
        self._update_collaboration_metrics(problem["id"], solution)

        return solution

    def _update_collaboration_metrics(
        self, problem_id: str, solution: Dict[str, Any]
    ) -> None:
        """
        Update collaboration metrics for a problem.

        Args:
            problem_id: ID of the problem
            solution: The collaborative solution
        """
        # Initialize metrics for this problem if they don't exist
        if problem_id not in self.collaboration_metrics:
            self.collaboration_metrics[problem_id] = {
                "start_time": datetime.now().isoformat(),
                "agent_contributions": {},
                "consensus_method": None,
                "conflicts_resolved": 0,
                "subtasks_completed": 0,
                "solution_quality": None,
            }

        metrics = self.collaboration_metrics[problem_id]

        # Update consensus method
        consensus = solution.get("consensus", {})
        metrics["consensus_method"] = consensus.get("method", "unknown")

        # Update conflicts resolved
        metrics["conflicts_resolved"] = consensus.get("conflicts_identified", 0)

        # Update subtasks completed
        metrics["subtasks_completed"] = len(solution.get("subtask_results", []))

        # Update agent contributions
        for agent in self.agents:
            if agent.name not in metrics["agent_contributions"]:
                metrics["agent_contributions"][agent.name] = {
                    "opinions_provided": 0,
                    "subtasks_completed": 0,
                    "conflicts_involved": 0,
                }

            # Count opinions
            if agent.name in consensus.get("agent_opinions", {}):
                metrics["agent_contributions"][agent.name]["opinions_provided"] += 1

            # Count subtasks
            for result in solution.get("subtask_results", []):
                if result.get("assigned_to") == agent.name:
                    metrics["agent_contributions"][agent.name][
                        "subtasks_completed"
                    ] += 1

        # Update solution quality (simplified)
        if "synthesis" in consensus:
            readability = consensus["synthesis"].get("readability_score", {})
            if readability:
                flesch_score = readability.get("flesch_reading_ease", 0)
                # Higher Flesch score is better (0-100)
                quality = min(100, max(0, flesch_score)) / 100
                metrics["solution_quality"] = quality

        # Update end time
        metrics["end_time"] = datetime.now().isoformat()

    def get_collaboration_metrics(self, problem_id: str) -> Dict[str, Any]:
        """
        Get collaboration metrics for a specific problem.

        Args:
            problem_id: ID of the problem

        Returns:
            Dictionary of collaboration metrics
        """
        return self.collaboration_metrics.get(problem_id, {})

    def get_role_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of role assignments in the team.

        Returns:
            List of role assignment events
        """
        return self.role_history

    def get_leadership_reassessment_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get the result of a leadership reassessment for a task.

        Args:
            task_id: ID of the task

        Returns:
            Leadership reassessment result
        """
        return self.leadership_reassessments.get(task_id, {})

    def get_transition_metrics(self, task_id: str) -> Dict[str, Any]:
        """
        Get transition metrics for a task.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary of transition metrics
        """
        return self.transition_metrics.get(task_id, {})

    def force_voting_tie(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Force a voting tie for testing purposes.

        Args:
            task: The task to force a tie for

        Returns:
            The voting result with a tie
        """
        # This method is primarily for testing the tie-breaking functionality

        # Ensure task has an ID
        if "id" not in task:
            task["id"] = str(uuid.uuid4())

        # Create equal number of votes for two options
        option1 = "Option A"
        option2 = "Option B"

        # Split agents evenly between options
        half_agents = len(self.agents) // 2

        # Assign votes
        votes = {}
        for i, agent in enumerate(self.agents):
            if i < half_agents:
                votes[agent.name] = option1
            else:
                votes[agent.name] = option2

        # Create voting result
        voting_result = {
            "task_id": task["id"],
            "votes": votes,
            "options": [option1, option2],
            "tied": True,
            "tied_options": [option1, option2],
            "timestamp": datetime.now().isoformat(),
        }

        return voting_result

    def set_agent_opinion(self, agent: Any, option_id: str, opinion: str) -> None:
        """
        Set an agent's opinion on an option.

        Args:
            agent: The agent
            option_id: ID of the option
            opinion: The opinion (e.g., "support", "oppose", "neutral")
        """
        # Ensure agent exists
        if agent not in self.agents and agent.name not in [a.name for a in self.agents]:
            self.logger.warning(
                f"Agent {agent.name if hasattr(agent, 'name') else agent} not found in team"
            )
            return

        # Get agent name
        agent_name = agent.name if hasattr(agent, "name") else str(agent)

        # Send opinion as a message
        self.send_message(
            sender=agent_name,
            recipients=["system"],
            message_type="option_opinion",
            subject=f"Opinion on {option_id}",
            content={"option_id": option_id, "opinion": opinion},
        )

        self.logger.debug(f"Set agent {agent_name} opinion on {option_id} to {opinion}")

    def vote_with_role_reassignment(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Vote on a critical decision after dynamically reassigning roles."""
        if "id" not in task:
            task["id"] = str(uuid.uuid4())
        # Reassign roles to ensure primus matches task context
        if hasattr(self, "dynamic_role_reassignment"):
            try:
                self.dynamic_role_reassignment(task)
            except Exception:
                pass
        primus = self.get_primus()
        result = self.vote_on_critical_decision(task)
        self.role_history.append(
            {
                "task_id": task["id"],
                "primus": primus.name if primus else None,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return result
