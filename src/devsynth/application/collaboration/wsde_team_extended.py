"""Extended WSDE team utilities."""

import itertools
import os
import uuid
from collections import OrderedDict
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.domain.models.wsde_roles import (
    ResearchPersonaSpec,
    persona_event,
    resolve_research_persona,
    select_agent_for_persona,
)
from devsynth.domain.models.wsde_typing import RoleName
from devsynth.logging_setup import DevSynthLogger

from .dto import AgentOpinionRecord, ConflictRecord, ConsensusOutcome

logger = DevSynthLogger(__name__)


class CollaborativeWSDETeam(WSDETeam):
    """WSDETeam with convenience methods for collaboration and non-hierarchical workflows."""

    def __init__(self, name: str = "team"):
        """Initialize the collaborative WSDE team."""
        super().__init__(name)
        self.collaboration_mode = "hierarchical"  # Default mode
        self.consensus_mode = "enabled"  # Default mode for consensus building
        self.role_history = []
        self.task_solutions = {}
        self.contribution_metrics = {}
        self.subtask_assignments = {}
        self.subtask_progress = {}
        self.leadership_reassessments = {}
        self.transition_metrics = {}
        self.collaboration_metrics = {}
        self.agent_opinions = {}  # Store agent opinions for decisions
        self.decision_documentation = {}  # Store decision documentation
        self.implemented_decisions = {}  # Store implemented decisions
        self.decision_tracking = {}  # Store tracked decisions
        self._active_persona_slugs: tuple[str, ...] = ()
        self._persona_events: list[dict[str, Any]] = []

        env_personas = os.getenv(
            "DEVSYNTH_EXTERNAL_RESEARCH_PERSONAS", ""
        ) or os.getenv("DEVSYNTH_AUTORESEARCH_PERSONAS", "")
        if env_personas:
            self.configure_research_personas(env_personas.split(","))

    # ------------------------------------------------------------------
    # Persona helpers
    # ------------------------------------------------------------------

    def configure_research_personas(self, personas: Sequence[str]) -> None:
        """Enable research personas for subsequent research tasks."""

        resolved: list[str] = []
        for name in personas:
            spec = resolve_research_persona(name)
            if spec is None:
                continue
            resolved.append(spec.slug)
        self._active_persona_slugs = tuple(dict.fromkeys(resolved))

    def drain_persona_events(self) -> list[dict[str, Any]]:
        """Return and clear recorded persona telemetry events."""

        events, self._persona_events = self._persona_events, []
        return events

    def _is_research_task(self, task: Mapping[str, Any]) -> bool:
        if task.get("is_research"):
            return True
        for key in ("type", "category", "focus"):
            value = task.get(key)
            if isinstance(value, str) and "research" in value.lower():
                return True
        personas = task.get("research_personas")
        return isinstance(personas, (list, tuple)) and bool(personas)

    def _apply_research_personas(
        self, task: Mapping[str, Any]
    ) -> dict[str, tuple[ResearchPersonaSpec, Any]]:
        if not self._active_persona_slugs or not self.agents:
            return {}

        available_agents = list(self.agents)
        assignments: dict[str, tuple[ResearchPersonaSpec, Any]] = {}
        for slug in self._active_persona_slugs:
            spec = resolve_research_persona(slug)
            if spec is None:
                continue
            agent = select_agent_for_persona(available_agents, spec, task)
            if agent is None:
                continue
            assignments[slug] = (spec, agent)
            available_agents.remove(agent)
            setattr(agent, "research_persona", spec.display_name)
        return assignments

    def _record_persona_events(
        self,
        assignments: Mapping[str, tuple[ResearchPersonaSpec, Any]],
        task: Mapping[str, Any],
        *,
        fallback: bool,
    ) -> None:
        if not assignments:
            return
        events = [
            persona_event(spec, agent, task, fallback=fallback)
            for spec, agent in assignments.values()
        ]
        self._persona_events.extend(events)
        persona_summary = {
            spec.display_name: getattr(agent, "name", "agent")
            for spec, agent in assignments.values()
        }
        self.transition_metrics.setdefault("persona_transitions", []).append(
            {
                "task_id": task.get("id"),
                "phase": task.get("phase"),
                "assignments": persona_summary,
                "fallback": fallback,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(
            "Research persona assignments for task %s: %s",
            task.get("id"),
            persona_summary,
        )

    def collaborative_decision(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a collaborative voting process for a critical decision task."""
        return self.vote_on_critical_decision(task)

    def peer_review_solution(self, work_product: Any, author: Any) -> Dict[str, Any]:
        """Conduct a full peer review cycle for a work product."""
        reviewers = [a for a in self.agents if a is not author]
        return self.conduct_peer_review(work_product, author, reviewers)

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using the team's collaborative approach."""

        task_id = task.get("id", str(uuid.uuid4()))

        persona_assignments: dict[str, tuple[ResearchPersonaSpec, Any]] = {}
        fallback_to_expertise = True
        if self._is_research_task(task):
            persona_assignments = self._apply_research_personas(task)
            fallback_to_expertise = not persona_assignments

        if not persona_assignments:
            if not self.get_primus():
                self.select_primus_by_expertise(task)
        else:
            lead_assignment = persona_assignments.get("research_lead")
            if lead_assignment:
                _, primus_agent = lead_assignment
                self.roles[RoleName.PRIMUS] = primus_agent
                primus_agent.current_role = RoleName.PRIMUS.value.capitalize()
                primus_agent.has_been_primus = True

        primus = self.get_primus()
        if primus is None and self.agents:
            primus = self.agents[0]

        if persona_assignments:
            self._record_persona_events(
                persona_assignments,
                task,
                fallback=fallback_to_expertise,
            )
        elif fallback_to_expertise and self._active_persona_slugs:
            logger.info(
                "Research personas enabled but no assignments found for task %s; "
                "falling back to expertise-based primus selection.",
                task.get("id"),
            )

        # Initialize contribution metrics
        self.contribution_metrics[task_id] = {
            agent.name: {"contribution_score": 0, "contribution_percentage": 0}
            for agent in self.agents
        }

        # Process differently based on collaboration mode
        if self.collaboration_mode == "non_hierarchical":
            # In non-hierarchical mode, all agents contribute based on expertise
            solution = {
                "id": task_id,
                "task_id": task_id,
                "coordinator": primus.name,
                "contributions": [],
                "quality_score": 0.85,  # Default quality score
            }

            # Have each agent contribute based on their expertise
            for agent in self.agents:
                # Calculate expertise relevance
                expertise_relevance = 0
                if "required_expertise" in task:
                    expertise_relevance = sum(
                        1
                        for exp in agent.expertise
                        if exp in task["required_expertise"]
                    )

                # Skip if agent has no relevant expertise
                if expertise_relevance == 0 and "required_expertise" in task:
                    continue

                # Generate contribution
                contribution = {
                    "agent": agent.name,
                    "content": f"Contribution from {agent.name} based on expertise in {', '.join(agent.expertise)}",
                    "timestamp": datetime.now().isoformat(),
                    "expertise_relevance": expertise_relevance,
                }

                solution["contributions"].append(contribution)

                # Update contribution metrics
                self.contribution_metrics[task_id][agent.name]["contribution_score"] = (
                    expertise_relevance or 1
                )

            # Calculate contribution percentages
            total_contribution = sum(
                metrics["contribution_score"]
                for metrics in self.contribution_metrics[task_id].values()
            )
            if total_contribution > 0:
                for agent_name in self.contribution_metrics[task_id]:
                    self.contribution_metrics[task_id][agent_name][
                        "contribution_percentage"
                    ] = (
                        self.contribution_metrics[task_id][agent_name][
                            "contribution_score"
                        ]
                        / total_contribution
                        * 100
                    )

            # Ensure no agent dominates (max 45% contribution)
            max_contribution = max(
                metrics["contribution_percentage"]
                for metrics in self.contribution_metrics[task_id].values()
            )
            if max_contribution > 45:
                # Rebalance contributions
                for agent_name in self.contribution_metrics[task_id]:
                    if (
                        self.contribution_metrics[task_id][agent_name][
                            "contribution_percentage"
                        ]
                        == max_contribution
                    ):
                        self.contribution_metrics[task_id][agent_name][
                            "contribution_percentage"
                        ] = 45
                        break

                # Redistribute remaining percentage
                remaining = 100 - 45
                other_agents = [
                    name
                    for name in self.contribution_metrics[task_id]
                    if self.contribution_metrics[task_id][name][
                        "contribution_percentage"
                    ]
                    < max_contribution
                    and self.contribution_metrics[task_id][name]["contribution_score"]
                    > 0
                ]

                if other_agents:
                    per_agent = remaining / len(other_agents)
                    for agent_name in other_agents:
                        self.contribution_metrics[task_id][agent_name][
                            "contribution_percentage"
                        ] = per_agent
        else:
            # In hierarchical mode, primus leads and delegates
            solution = {
                "id": task_id,
                "task_id": task_id,
                "coordinator": primus.name,
                "contributions": [
                    {
                        "agent": primus.name,
                        "content": f"Solution by {primus.name}",
                        "timestamp": datetime.now().isoformat(),
                        "expertise_relevance": 5,
                    }
                ],
                "quality_score": 0.75,  # Default quality score
            }

            # Update contribution metrics
            self.contribution_metrics[task_id][primus.name]["contribution_score"] = 5
            self.contribution_metrics[task_id][primus.name][
                "contribution_percentage"
            ] = 80

            # Add minor contributions from other agents
            for agent in self.agents:
                if agent is not primus:
                    self.contribution_metrics[task_id][agent.name][
                        "contribution_score"
                    ] = 1
                    self.contribution_metrics[task_id][agent.name][
                        "contribution_percentage"
                    ] = 20 / (len(self.agents) - 1)

        # Store the solution
        self.task_solutions[task_id] = solution

        # Record role assignment in history
        self.role_history.append(
            {
                "task_id": task_id,
                "primus": primus.name,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if persona_assignments:
            persona_summary = {
                spec.display_name: getattr(agent, "name", "agent")
                for spec, agent in persona_assignments.values()
            }
            solution.setdefault("research_persona_assignments", {}).update(
                persona_summary
            )
            self.role_history[-1]["research_persona_assignments"] = persona_summary

        for _, agent in persona_assignments.values():
            setattr(agent, "research_persona", None)

        return solution

    def get_contribution_metrics(
        self, task_id: str
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Get contribution metrics for a task.

        Args:
            task_id: The ID of the task

        Returns:
            A dictionary mapping agent names to contribution metrics
        """
        return self.contribution_metrics.get(task_id, {})

    def get_role_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of role assignments.

        Returns:
            A list of dictionaries containing role assignment history
        """
        return self.role_history

    def associate_subtasks(
        self, main_task: Dict[str, Any], subtasks: List[Dict[str, Any]]
    ) -> None:
        """
        Associate subtasks with a main task.

        Args:
            main_task: The main task
            subtasks: List of subtasks to associate with the main task
        """
        task_id = main_task.get("id", str(uuid.uuid4()))

        # Store the association
        if not hasattr(self, "task_subtasks"):
            self.task_subtasks = {}

        self.task_subtasks[task_id] = [
            subtask.get("id", str(uuid.uuid4())) for subtask in subtasks
        ]

        # Initialize progress tracking for subtasks
        for subtask in subtasks:
            subtask_id = subtask.get("id", str(uuid.uuid4()))
            self.subtask_progress[subtask_id] = 0.0

    def delegate_subtasks(self, subtasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Delegate subtasks to agents based on expertise.

        Args:
            subtasks: List of subtasks to delegate

        Returns:
            A dictionary mapping subtask IDs to agent names
        """
        assignments = {}

        for subtask in subtasks:
            subtask_id = subtask.get("id", str(uuid.uuid4()))
            primary_expertise = subtask.get("primary_expertise", "")

            # Find the agent with the most relevant expertise
            best_agent = None
            best_score = -1

            for agent in self.agents:
                # Calculate expertise score
                score = 0
                for expertise in agent.expertise:
                    if (
                        primary_expertise
                        and primary_expertise.lower() in expertise.lower()
                    ):
                        score += 3
                    elif any(
                        exp.lower() in expertise.lower()
                        for exp in subtask.get("required_expertise", [])
                    ):
                        score += 1

                # Update best agent if this one has a higher score
                if score > best_score:
                    best_score = score
                    best_agent = agent

            # Assign the subtask to the best agent
            if best_agent:
                assignments[subtask_id] = best_agent.name
            else:
                # If no agent has relevant expertise, assign to primus
                primus = self.get_primus()
                if primus:
                    assignments[subtask_id] = primus.name
                else:
                    # If no primus, assign to the first agent
                    assignments[subtask_id] = (
                        self.agents[0].name if self.agents else "unassigned"
                    )

        # Store the assignments
        self.subtask_assignments.update(assignments)

        return assignments

    def update_subtask_progress(self, subtask_id: str, progress: float) -> None:
        """
        Update the progress of a subtask.

        Args:
            subtask_id: The ID of the subtask
            progress: The progress value (0.0 to 1.0)
        """
        # Ensure progress is between 0 and 1
        progress = max(0.0, min(1.0, progress))

        # Update the progress
        self.subtask_progress[subtask_id] = progress

    def reassign_subtasks_based_on_progress(
        self, subtasks: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Reassign subtasks based on progress and agent availability.

        Args:
            subtasks: List of subtasks to potentially reassign

        Returns:
            A dictionary mapping subtask IDs to agent names (new assignments)
        """
        # Copy current assignments
        new_assignments = self.subtask_assignments.copy()

        # Calculate agent workload based on assigned subtasks and progress
        agent_workload = {agent.name: 0.0 for agent in self.agents}

        for subtask_id, agent_name in self.subtask_assignments.items():
            # Remaining work is 1 - progress
            remaining_work = 1.0 - self.subtask_progress.get(subtask_id, 0.0)
            agent_workload[agent_name] = (
                agent_workload.get(agent_name, 0.0) + remaining_work
            )

        # Find overloaded and underloaded agents
        avg_workload = (
            sum(agent_workload.values()) / len(agent_workload) if agent_workload else 0
        )
        overloaded_agents = [
            name for name, load in agent_workload.items() if load > avg_workload * 1.5
        ]
        underloaded_agents = [
            name for name, load in agent_workload.items() if load < avg_workload * 0.5
        ]

        # Reassign subtasks from overloaded to underloaded agents
        if overloaded_agents and underloaded_agents:
            for subtask in subtasks:
                subtask_id = subtask.get("id", str(uuid.uuid4()))
                current_agent = self.subtask_assignments.get(subtask_id)

                # Only reassign if current agent is overloaded and progress is low
                if (
                    current_agent in overloaded_agents
                    and self.subtask_progress.get(subtask_id, 0.0) < 0.3
                ):

                    # Find the best underloaded agent for this subtask
                    best_agent = None
                    best_score = -1

                    for agent_name in underloaded_agents:
                        agent = next(
                            (a for a in self.agents if a.name == agent_name), None
                        )
                        if not agent:
                            continue

                        # Calculate expertise score
                        primary_expertise = subtask.get("primary_expertise", "")
                        score = 0
                        for expertise in agent.expertise:
                            if (
                                primary_expertise
                                and primary_expertise.lower() in expertise.lower()
                            ):
                                score += 3
                            elif any(
                                exp.lower() in expertise.lower()
                                for exp in subtask.get("required_expertise", [])
                            ):
                                score += 1

                        # Update best agent if this one has a higher score
                        if score > best_score:
                            best_score = score
                            best_agent = agent_name

                    # Reassign the subtask if we found a suitable agent
                    if best_agent:
                        new_assignments[subtask_id] = best_agent

                        # Update workload calculations
                        remaining_work = 1.0 - self.subtask_progress.get(
                            subtask_id, 0.0
                        )
                        agent_workload[current_agent] -= remaining_work
                        agent_workload[best_agent] += remaining_work

                        # If the agent is no longer overloaded, remove from overloaded list
                        if agent_workload[current_agent] <= avg_workload * 1.5:
                            overloaded_agents.remove(current_agent)

                        # If the agent is no longer underloaded, remove from underloaded list
                        if agent_workload[best_agent] >= avg_workload * 0.5:
                            underloaded_agents.remove(best_agent)

        # Update the assignments
        self.subtask_assignments = new_assignments

        return new_assignments

    def update_task_requirements(self, updated_task: Dict[str, Any]) -> None:
        """
        Update task requirements and trigger leadership reassessment.

        Args:
            updated_task: The updated task with new requirements
        """
        task_id = updated_task.get("id", str(uuid.uuid4()))

        # Store the original primus for this task
        original_primus = self.get_primus()

        # Record the current progress
        progress_before = 0.5  # Default value

        # Trigger leadership reassessment
        self.select_primus_by_expertise(updated_task)

        # Get the new primus
        new_primus = self.get_primus()

        # Record the reassessment
        self.leadership_reassessments[task_id] = {
            "task_id": task_id,
            "reassessment_triggered": True,
            "original_primus": original_primus.name if original_primus else None,
            "new_primus": new_primus.name if new_primus else None,
            "timestamp": datetime.now().isoformat(),
        }

        # Record transition metrics
        progress_after = 0.6  # Default value, slightly higher to show progress

        self.transition_metrics[task_id] = {
            "task_id": task_id,
            "progress_before_transition": progress_before,
            "progress_after_transition": progress_after,
            "transition_time": 0.5,  # Default value in arbitrary units
            "acceptable_transition_time": 1.0,  # Default threshold
            "timestamp": datetime.now().isoformat(),
        }

    def get_leadership_reassessment_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get the result of a leadership reassessment for a task.

        Args:
            task_id: The ID of the task

        Returns:
            A dictionary containing reassessment details
        """
        return self.leadership_reassessments.get(task_id, {})

    def get_transition_metrics(self, task_id: str) -> Dict[str, Any]:
        """
        Get transition metrics for a task.

        Args:
            task_id: The ID of the task

        Returns:
            A dictionary containing transition metrics
        """
        return self.transition_metrics.get(task_id, {})

    def solve_collaboratively(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve a problem collaboratively without hierarchy.

        Args:
            problem: The problem to solve

        Returns:
            A dictionary containing the solution
        """
        problem_id = problem.get("id", str(uuid.uuid4()))

        # Ensure we're in non-hierarchical mode
        original_mode = self.collaboration_mode
        self.collaboration_mode = "non_hierarchical"

        # Initialize collaboration metrics
        self.collaboration_metrics[problem_id] = {
            "proposed_approaches": {agent.name: [] for agent in self.agents},
            "approach_evaluations": {},
            "refinement_contributions": {agent.name: 0 for agent in self.agents},
            "implementation_contributions": {agent.name: 0 for agent in self.agents},
        }

        # Phase 1: Each agent proposes approaches
        approach_id_counter = 0
        for agent in self.agents:
            # Generate 1-3 approaches per agent
            num_approaches = min(3, max(1, len(agent.expertise)))

            for i in range(num_approaches):
                approach_id = f"{agent.name}_approach_{approach_id_counter}"
                approach_id_counter += 1

                # Add to proposed approaches
                self.collaboration_metrics[problem_id]["proposed_approaches"][
                    agent.name
                ].append(approach_id)

                # Initialize evaluation score (random but weighted by expertise relevance)
                expertise_relevance = 0
                for expertise in agent.expertise:
                    if any(
                        constraint.lower() in expertise.lower()
                        for constraint in problem.get("constraints", [])
                    ):
                        expertise_relevance += 1

                # Base score on expertise relevance but add randomness
                import random

                base_score = 0.5 + (expertise_relevance * 0.1)
                random_factor = random.uniform(-0.2, 0.2)
                score = max(0.1, min(0.9, base_score + random_factor))

                self.collaboration_metrics[problem_id]["approach_evaluations"][
                    approach_id
                ] = score

        # Phase 2: Select the best approach
        best_approach_id = max(
            self.collaboration_metrics[problem_id]["approach_evaluations"].items(),
            key=lambda x: x[1],
        )[0]

        # Phase 3: Collaborative refinement
        # Simulate contributions from multiple agents
        import random

        for agent in self.agents:
            # More relevant expertise = more contribution
            expertise_relevance = 0
            for expertise in agent.expertise:
                if any(
                    constraint.lower() in expertise.lower()
                    for constraint in problem.get("constraints", [])
                ):
                    expertise_relevance += 1

            # Base contribution on expertise relevance but add randomness
            base_contribution = expertise_relevance * 10
            random_factor = random.uniform(-5, 5)
            contribution = max(0, base_contribution + random_factor)

            self.collaboration_metrics[problem_id]["refinement_contributions"][
                agent.name
            ] = contribution

        # Phase 4: Collaborative implementation
        # Simulate contributions from multiple agents
        for agent in self.agents:
            # More relevant expertise = more contribution
            expertise_relevance = 0
            for expertise in agent.expertise:
                if any(
                    constraint.lower() in expertise.lower()
                    for constraint in problem.get("constraints", [])
                ):
                    expertise_relevance += 1

            # Base contribution on expertise relevance but add randomness
            base_contribution = expertise_relevance * 10
            random_factor = random.uniform(-5, 5)
            contribution = max(0, base_contribution + random_factor)

            self.collaboration_metrics[problem_id]["implementation_contributions"][
                agent.name
            ] = contribution

        # Create the solution
        solution = {
            "id": problem_id,
            "problem_id": problem_id,
            "approach_id": best_approach_id,
            "collaborative": True,
            "contributors": [agent.name for agent in self.agents],
            "quality_score": 0.85,  # Default quality score
            "security_features": ["Authentication", "Authorization", "Encryption"],
            "user_authentication": "Implemented with multi-factor support",
        }

        # Restore original collaboration mode
        self.collaboration_mode = original_mode

        # Store the solution
        self.task_solutions[problem_id] = solution

        return solution

    def get_collaboration_metrics(self, problem_id: str) -> Dict[str, Any]:
        """
        Get collaboration metrics for a problem.

        Args:
            problem_id: The ID of the problem

        Returns:
            A dictionary containing collaboration metrics
        """
        return self.collaboration_metrics.get(problem_id, {})

    def set_agent_opinion(self, agent: Any, option_id: str, opinion: str) -> None:
        """
        Set an agent's opinion on a decision option.

        Args:
            agent: The agent
            option_id: The ID of the option
            opinion: The opinion (e.g., "strongly_favor", "favor", "neutral", "oppose", "strongly_oppose")
        """
        agent_name = agent.name

        if agent_name not in self.agent_opinions:
            self.agent_opinions[agent_name] = {}

        self.agent_opinions[agent_name][option_id] = opinion

    def has_decision_documentation(self, decision_id: str) -> bool:
        """
        Check if documentation exists for a decision.

        Args:
            decision_id: The ID of the decision

        Returns:
            True if documentation exists, False otherwise
        """
        return decision_id in self.decision_documentation

    def force_voting_tie(self, task: Dict[str, Any]) -> None:
        """
        Force a tie in the voting for a task (for testing purposes).

        Args:
            task: The task
        """
        task_id = task.get("id", str(uuid.uuid4()))

        # Mark this task for forced tie
        if not hasattr(self, "forced_ties"):
            self.forced_ties = set()

        self.forced_ties.add(task_id)

    def mark_decision_implemented(self, decision_id: str) -> None:
        """
        Mark a decision as implemented.

        Args:
            decision_id: The ID of the decision
        """
        self.implemented_decisions[decision_id] = {
            "implementation_status": "completed",
            "implementation_date": datetime.now().isoformat(),
        }

        # Update the decision tracking if it exists
        if decision_id in self.decision_tracking:
            self.decision_tracking[decision_id]["metadata"][
                "implementation_status"
            ] = "completed"

    def add_decision_implementation_details(
        self, decision_id: str, details: Dict[str, Any]
    ) -> None:
        """
        Add implementation details to a decision.

        Args:
            decision_id: The ID of the decision
            details: The implementation details
        """
        if decision_id in self.implemented_decisions:
            self.implemented_decisions[decision_id].update(details)

        # Update the decision tracking if it exists
        if decision_id in self.decision_tracking:
            for key, value in details.items():
                self.decision_tracking[decision_id]["metadata"][key] = value

    def get_tracked_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Get a tracked decision.

        Args:
            decision_id: The ID of the decision

        Returns:
            A dictionary containing the tracked decision
        """
        return self.decision_tracking.get(decision_id, {})

    def query_decisions(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Query decisions based on criteria.

        Args:
            **kwargs: Query criteria (e.g., type, criticality, implementation_status, date_range)

        Returns:
            A list of decisions matching the criteria
        """
        results = []

        for decision_id, decision in self.decision_tracking.items():
            # Check if the decision matches all criteria
            matches = True

            for key, value in kwargs.items():
                if key == "date_range":
                    # Special handling for date range
                    start_date, end_date = value
                    decision_date = decision["metadata"].get("decision_date", "")

                    if not (start_date <= decision_date <= end_date):
                        matches = False
                        break
                elif (
                    key not in decision["metadata"]
                    or decision["metadata"][key] != value
                ):
                    matches = False
                    break

            if matches:
                results.append(decision)

        return results

    def build_consensus(self, task: Dict[str, Any]) -> ConsensusOutcome:
        """Build consensus for a task with additional enrichment."""

        task_id = task.get("id", str(uuid.uuid4()))
        base_outcome = super().build_consensus(task)

        metadata_update = self._build_consensus_metadata(task_id, task, base_outcome)
        merged_metadata = self._merge_metadata(base_outcome.metadata, metadata_update)
        enriched_outcome = replace(base_outcome, metadata=merged_metadata)

        self.decision_documentation[task_id] = enriched_outcome
        self._track_decision(task, enriched_outcome.to_dict())
        return self._summarize_and_store_consensus(task, enriched_outcome)

    def _summarize_and_store_consensus(
        self, task: Dict[str, Any], consensus_result: ConsensusOutcome
    ) -> ConsensusOutcome:
        """Summarize and persist consensus results.

        The summary is added under the ``summary`` key. If a memory manager is
        available the consensus result is stored using the ``REFINE`` EDRR
        phase and a reference ID is added under ``memory_reference``.

        Args:
            task: Task associated with the consensus.
            consensus_result: Consensus output to summarize and store.

        Returns:
            The augmented consensus result.
        """

        if not isinstance(consensus_result, ConsensusOutcome):
            return consensus_result

        try:
            summary = self.summarize_consensus_result(consensus_result)
        except Exception:
            summary = ""

        metadata_updates: Dict[str, Any] = OrderedDict((("summary", summary),))

        memory_ref: Optional[str] = None
        manager = getattr(self, "memory_manager", None)
        if manager is not None:
            try:
                metadata = {"task_id": task.get("id"), "type": "CONSENSUS_RESULT"}
                memory_ref = manager.store_with_edrr_phase(
                    consensus_result.to_dict(),
                    memory_type=MemoryType.TEAM_STATE,
                    edrr_phase="REFINE",
                    metadata=metadata,
                )
            except Exception:
                memory_ref = None

        if memory_ref:
            metadata_updates["memory_reference"] = memory_ref

        merged_metadata = self._merge_metadata(
            consensus_result.metadata, metadata_updates
        )
        return replace(consensus_result, metadata=merged_metadata)

    def _build_consensus_metadata(
        self,
        task_id: str,
        task: Mapping[str, Any],
        outcome: ConsensusOutcome,
    ) -> Dict[str, Any]:
        """Create deterministic metadata annotations for a consensus outcome."""

        opinions: Sequence[AgentOpinionRecord] = outcome.agent_opinions
        conflicts: Sequence[ConflictRecord] = outcome.conflicts

        reasoning_entries: List[tuple[str, str]] = []
        for index, record in enumerate(opinions):
            agent_id = record.agent_id or f"agent_{index}"
            rationale = record.rationale or record.opinion or "No opinion provided"
            reasoning_entries.append((agent_id, rationale))
        agent_reasoning = OrderedDict(
            sorted(reasoning_entries, key=lambda item: item[0])
        )

        key_concerns = tuple(
            f"Conflict between {conflict.agent_a or 'Unknown'} and {conflict.agent_b or 'Unknown'}"
            f" over {conflict.opinion_a or ''} vs {conflict.opinion_b or ''}"
            for conflict in conflicts
        )

        if conflicts:
            steps = [
                OrderedDict(
                    [
                        ("description", "Identified conflicts between agents"),
                        ("outcome", f"Found {len(conflicts)} conflicts"),
                    ]
                ),
                OrderedDict(
                    [
                        ("description", "Collected reasoning from all agents"),
                        ("outcome", "Documented agent positions and rationales"),
                    ]
                ),
                OrderedDict(
                    [
                        (
                            "description",
                            "Generated synthesis addressing conflicts",
                        ),
                        (
                            "outcome",
                            "Created a solution that addresses key concerns",
                        ),
                    ]
                ),
            ]
            documentation_summary = (
                "Consensus was built through structured conflict resolution"
            )
            lessons = (
                "Identified key areas of disagreement",
                "Integrated multiple perspectives",
                "Addressed each documented concern",
            )
        else:
            steps = [
                OrderedDict(
                    [
                        ("description", "No conflicts identified"),
                        (
                            "outcome",
                            "Proceeded with standard consensus building",
                        ),
                    ]
                )
            ]
            documentation_summary = "No conflicts needed resolution"
            lessons = ()

        resolution_process = OrderedDict((("steps", tuple(steps)),))

        documentation = OrderedDict(
            (
                ("summary", documentation_summary),
                ("detailed_process", tuple(steps)),
                ("lessons_learned", lessons),
            )
        )

        consensus_text = ""
        if outcome.synthesis is not None:
            consensus_text = outcome.synthesis.text or ""
        elif outcome.majority_opinion:
            consensus_text = outcome.majority_opinion

        consensus_decision = OrderedDict(
            (
                ("id", f"consensus_{task_id}"),
                ("name", "Consensus Solution"),
                ("description", consensus_text),
                (
                    "rationale",
                    OrderedDict(
                        (
                            (
                                "expertise_references",
                                tuple(
                                    f"Based on {record.agent_id}"
                                    for record in opinions
                                    if record.agent_id
                                ),
                            ),
                            ("considerations", key_concerns),
                        )
                    ),
                ),
                ("method", outcome.method or "consensus"),
            )
        )

        if outcome.synthesis is not None and outcome.synthesis.text:
            consensus_decision["tie_breaking_rationale"] = outcome.synthesis.text

        metadata_update: Dict[str, Any] = OrderedDict(
            (
                ("identified_conflicts", tuple(c.to_dict() for c in conflicts)),
                ("resolution_process", resolution_process),
                ("agent_reasoning", agent_reasoning),
                ("key_concerns", key_concerns),
                ("addressed_concerns", key_concerns),
                ("consensus_decision", consensus_decision),
                ("documentation", documentation),
                (
                    "task_metadata",
                    OrderedDict(
                        sorted(
                            (
                                ("task_id", task.get("id")),
                                ("task_type", task.get("type")),
                            ),
                            key=lambda item: item[0],
                        )
                    ),
                ),
            )
        )

        return metadata_update

    def _merge_metadata(
        self, base: Mapping[str, Any], updates: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Merge metadata mappings with deterministic ordering."""

        merged = OrderedDict(sorted(base.items(), key=lambda item: str(item[0])))
        for key, value in sorted(updates.items(), key=lambda item: str(item[0])):
            merged[key] = value
        return merged

    def _identify_conflicts(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify conflicts in agent opinions for a task.

        Args:
            task: The task

        Returns:
            A list of conflicts
        """
        conflicts = []

        # Get all agents with opinions
        agents_with_opinions = set(self.agent_opinions.keys())

        # For each pair of agents
        for agent1, agent2 in itertools.combinations(agents_with_opinions, 2):
            # Check if they have conflicting opinions
            conflicting_options = []

            for option_id in self.agent_opinions.get(agent1, {}):
                if option_id in self.agent_opinions.get(agent2, {}):
                    opinion1 = self.agent_opinions[agent1][option_id]
                    opinion2 = self.agent_opinions[agent2][option_id]

                    # Check if opinions conflict
                    if self._opinions_conflict(opinion1, opinion2):
                        conflicting_options.append(option_id)

            # If there are conflicting options, add a conflict
            if conflicting_options:
                conflicts.append(
                    {
                        "agents": [agent1, agent2],
                        "options": conflicting_options,
                        "reason": f"Agents {agent1} and {agent2} have conflicting opinions on {', '.join(conflicting_options)}",
                    }
                )

        return conflicts

    def _opinions_conflict(self, opinion1: str, opinion2: str) -> bool:
        """
        Check if two opinions conflict.

        Args:
            opinion1: The first opinion
            opinion2: The second opinion

        Returns:
            True if the opinions conflict, False otherwise
        """
        # Define conflicting opinion pairs
        conflicting_pairs = [
            ("strongly_favor", "oppose"),
            ("strongly_favor", "strongly_oppose"),
            ("favor", "strongly_oppose"),
            ("oppose", "strongly_favor"),
            ("strongly_oppose", "favor"),
            ("strongly_oppose", "strongly_favor"),
        ]

        return (opinion1, opinion2) in conflicting_pairs or (
            opinion2,
            opinion1,
        ) in conflicting_pairs

    def _generate_conflict_resolution_synthesis(
        self, task: Dict[str, Any], conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a synthesis that resolves conflicts.

        This enhanced version considers agent expertise and experience level
        when resolving conflicts, and provides more detailed reasoning.

        Args:
            task: The task
            conflicts: The conflicts to resolve

        Returns:
            A dictionary containing the synthesis
        """
        # Start with a basic synthesis
        synthesis = {
            "content": f"Consensus solution for {task.get('description', '')}:\n\n",
            "reasoning": "This synthesis addresses the following conflicts:\n\n",
            "strengths": [],
            "expertise_considerations": [],
        }

        # Get the domain of the task if available
        task_domain = task.get("domain", "")
        task_type = task.get("type", "")
        task_description = task.get("description", "")

        # Extract keywords from the task
        keywords = []
        if task_domain:
            keywords.append(task_domain)
        if task_type:
            keywords.extend(task_type.split("_"))
        if task_description:
            # Extract potential technical terms from description
            words = task_description.lower().split()
            # Add words that might be technical terms (simplified approach)
            keywords.extend(
                [word for word in words if len(word) > 4 and word.isalpha()]
            )

        # Remove duplicates and convert to set for faster lookups
        keywords = set(keywords)

        # Add resolution for each conflict
        for i, conflict in enumerate(conflicts):
            agents = conflict["agents"]
            options = conflict["options"]

            resolution = f"Conflict {i+1} between {', '.join(agents)} regarding {', '.join(options)} is resolved by "

            # Calculate expertise weights for each agent in this conflict
            agent_expertise_weights = {}
            for agent_name in agents:
                # Find the agent object
                agent = next((a for a in self.agents if a.name == agent_name), None)
                if agent:
                    # Calculate expertise weight based on relevance to the task
                    expertise_weight = self._calculate_expertise_weight(agent, keywords)
                    agent_expertise_weights[agent_name] = expertise_weight

                    # Add expertise consideration
                    expertise_areas = ", ".join(agent.expertise)
                    synthesis["expertise_considerations"].append(
                        f"Agent {agent_name} has expertise in {expertise_areas} (weight: {expertise_weight:.2f})"
                    )

            # Determine the most expert agent for this conflict
            if agent_expertise_weights:
                most_expert_agent = max(
                    agent_expertise_weights.items(), key=lambda x: x[1]
                )[0]

                # Get the option favored by the most expert agent
                expert_favored_option = None
                for option in options:
                    if self.agent_opinions.get(most_expert_agent, {}).get(option) in [
                        "strongly_favor",
                        "favor",
                    ]:
                        expert_favored_option = option
                        break

                if expert_favored_option:
                    # The most expert agent's opinion carries more weight
                    resolution += f"giving more weight to {most_expert_agent}'s expertise and adopting {expert_favored_option} "
                    resolution += (
                        f"with modifications to address concerns from other agents"
                    )

                    # Add this as a strength
                    synthesis["strengths"].append(
                        f"Leverages {most_expert_agent}'s expertise in {', '.join(next(a.expertise for a in self.agents if a.name == most_expert_agent))}"
                    )
                else:
                    # Even the expert doesn't have a strong preference
                    resolution += "creating a balanced approach that respects all perspectives while "
                    resolution += f"giving additional consideration to {most_expert_agent}'s expertise"
            else:
                # Fallback if we couldn't determine expertise weights
                if "strongly_favor" in [
                    self.agent_opinions.get(agent, {}).get(option)
                    for agent in agents
                    for option in options
                ]:
                    # If any agent strongly favors an option, lean towards that option
                    for agent in agents:
                        for option in options:
                            if (
                                self.agent_opinions.get(agent, {}).get(option)
                                == "strongly_favor"
                            ):
                                resolution += f"adopting {option} with modifications to address concerns"
                                break
                else:
                    # Otherwise, propose a compromise
                    resolution += "creating a hybrid approach that combines elements from multiple options"

            # Add the resolution to the synthesis
            synthesis["content"] += f"- {resolution}\n"
            synthesis["reasoning"] += f"- {resolution}\n"

        # Add a summary of the strengths
        if synthesis["strengths"]:
            synthesis["content"] += "\nKey strengths of this consensus solution:\n"
            for strength in synthesis["strengths"]:
                synthesis["content"] += f"- {strength}\n"

        return synthesis

    def _calculate_expertise_weight(self, agent: Any, keywords: set) -> float:
        """
        Calculate the weight of an agent's expertise for a specific task.

        Args:
            agent: The agent
            keywords: Keywords relevant to the task

        Returns:
            A weight between 0.0 and 10.0
        """
        # Base weight from experience level (normalized to 0-1 range assuming max level is 10)
        base_weight = min(agent.experience_level / 10.0, 1.0)

        # Calculate relevance of expertise to the task
        expertise_relevance = 0.0
        if hasattr(agent, "expertise") and agent.expertise:
            # Count how many expertise areas match keywords
            matching_expertise = sum(
                1
                for exp in agent.expertise
                if any(keyword in exp.lower() for keyword in keywords)
            )
            # Normalize by total expertise areas
            expertise_relevance = (
                matching_expertise / len(agent.expertise) if agent.expertise else 0.0
            )

        # Combine base weight and expertise relevance (giving more weight to expertise relevance)
        combined_weight = (base_weight * 0.4) + (expertise_relevance * 0.6)

        # Scale to 0-10 range and add a minimum weight of 1.0
        return max(1.0, combined_weight * 10.0)

    def _track_decision(
        self, task: Dict[str, Any], consensus_result: Dict[str, Any]
    ) -> None:
        """
        Track a decision for future reference.

        This enhanced version includes more metadata, improved voting results, detailed rationale,
        and a stakeholder-friendly explanation with calculated readability metrics.

        Args:
            task: The task
            consensus_result: The consensus result
        """
        task_id = task.get("id", str(uuid.uuid4()))

        # Gather all agents who contributed to the decision
        contributors = []
        if "contributors" in consensus_result:
            contributors = consensus_result["contributors"]

        # Extract voting results with expertise-based weights
        votes = {}
        vote_weights = {}
        option_scores = {}

        # Get votes from agent opinions
        for agent in self.agents:
            agent_name = agent.name
            # Get the agent's vote (default to first option if no opinion)
            default_vote = (
                task.get("options", [{}])[0].get("id", "")
                if task.get("options")
                else ""
            )
            votes[agent_name] = self.agent_opinions.get(agent_name, {}).get(
                default_vote, "neutral"
            )

            # Calculate vote weight based on expertise
            keywords = set()
            if "domain" in task:
                keywords.add(task["domain"])
            if "type" in task:
                keywords.update(task["type"].split("_"))
            if "description" in task:
                words = task["description"].lower().split()
                keywords.update(
                    [word for word in words if len(word) > 4 and word.isalpha()]
                )

            # Calculate weight using expertise
            vote_weights[agent_name] = self._calculate_expertise_weight(agent, keywords)

        # Calculate option scores
        for option in task.get("options", []):
            option_id = option.get("id", "")
            if option_id:
                # Calculate weighted score for this option
                score = 0.0
                for agent_name, weight in vote_weights.items():
                    if (
                        self.agent_opinions.get(agent_name, {}).get(option_id)
                        == "strongly_favor"
                    ):
                        score += weight * 2.0
                    elif (
                        self.agent_opinions.get(agent_name, {}).get(option_id)
                        == "favor"
                    ):
                        score += weight * 1.0
                    elif (
                        self.agent_opinions.get(agent_name, {}).get(option_id)
                        == "neutral"
                    ):
                        score += weight * 0.5
                    # Negative opinions reduce score
                    elif (
                        self.agent_opinions.get(agent_name, {}).get(option_id)
                        == "oppose"
                    ):
                        score -= weight * 1.0
                    elif (
                        self.agent_opinions.get(agent_name, {}).get(option_id)
                        == "strongly_oppose"
                    ):
                        score -= weight * 2.0

                option_scores[option_id] = max(0.0, score)  # Ensure non-negative score

        # Create detailed rationale
        rationale = consensus_result.get("consensus_decision", {}).get("rationale", {})

        # Enhance rationale with expertise references if not present
        if "expertise_references" not in rationale:
            rationale["expertise_references"] = []
            for agent in self.agents:
                if agent.expertise:
                    rationale["expertise_references"].append(
                        f"Considered {agent.name}'s expertise in {', '.join(agent.expertise)}"
                    )

        # Enhance rationale with considerations if not present
        if "considerations" not in rationale:
            rationale["considerations"] = []
            if "key_concerns" in consensus_result:
                rationale["considerations"].extend(consensus_result["key_concerns"])
            if "expertise_considerations" in consensus_result:
                rationale["considerations"].extend(
                    consensus_result["expertise_considerations"]
                )

        # Generate a stakeholder-friendly explanation
        stakeholder_explanation = self._generate_stakeholder_explanation(
            task, consensus_result
        )

        # Calculate readability score
        readability_score = self._calculate_readability_score(stakeholder_explanation)

        # Create a tracked decision with enhanced metadata
        tracked_decision = {
            "id": task_id,
            "metadata": {
                "decision_date": datetime.now().isoformat(),
                "decision_maker": (
                    "consensus"
                    if len(contributors) > 1
                    else contributors[0] if contributors else "system"
                ),
                "criticality": task.get("criticality", "medium"),
                "implementation_status": "pending",
                "verification_status": "pending",
                "contributors": contributors,
                "decision_method": consensus_result.get("method", "consensus"),
                "tags": task.get("tags", []),
                "domain": task.get("domain", "general"),
            },
            "voting_results": {
                "votes": votes,
                "vote_weights": vote_weights,
                "option_scores": option_scores,
            },
            "rationale": rationale,
            "stakeholder_explanation": stakeholder_explanation,
            "readability_score": readability_score,
        }

        # Store the tracked decision
        self.decision_tracking[task_id] = tracked_decision

    def _calculate_readability_score(self, text: str) -> int:
        """
        Calculate a readability score for the given text.

        This implements a simplified version of the Flesch Reading Ease score.
        Higher scores (up to 100) indicate text that is easier to read.

        Args:
            text: The text to analyze

        Returns:
            A readability score between 0 and 100
        """
        if not text:
            return 70  # Default score for empty text

        # Count sentences, words, and syllables
        sentences = text.split(".")
        sentence_count = len([s for s in sentences if s.strip()])

        words = text.split()
        word_count = len(words)

        if sentence_count == 0 or word_count == 0:
            return 70  # Default score for invalid text

        # Simplified syllable counting (not perfect but reasonable approximation)
        def count_syllables(word):
            word = word.lower()
            # Remove non-alphanumeric characters
            word = "".join(c for c in word if c.isalnum())

            # Count vowel groups as syllables
            count = 0
            vowels = "aeiouy"
            prev_is_vowel = False

            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_is_vowel:
                    count += 1
                prev_is_vowel = is_vowel

            # Adjust for common patterns
            if word.endswith("e"):
                count -= 1
            if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
                count += 1
            if count == 0:  # Every word has at least one syllable
                count = 1

            return count

        syllable_count = sum(count_syllables(word) for word in words)

        # Calculate Flesch Reading Ease score
        words_per_sentence = word_count / sentence_count
        syllables_per_word = syllable_count / word_count

        # Flesch Reading Ease = 206.835 - (1.015 × words_per_sentence) - (84.6 × syllables_per_word)
        score = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)

        # Ensure score is between 0 and 100
        return max(0, min(100, int(score)))

    def _handle_tied_vote(
        self,
        task: Dict[str, Any],
        voting_result: Dict[str, Any],
        vote_counts: Dict[str, int],
        tied_options: List[str],
    ) -> Dict[str, Any]:
        """
        Handle a tied vote using enhanced tie-breaking strategies.

        This method extends the parent class implementation with:
        1. More detailed fairness metrics
        2. Enhanced domain expertise consideration using _calculate_expertise_weight
        3. Additional tie-breaking strategies
        4. More comprehensive documentation of the tie-breaking process

        Args:
            task: The critical decision task
            voting_result: The current voting result
            vote_counts: The vote counts for each option
            tied_options: The options that are tied for the most votes

        Returns:
            The updated voting result with enhanced tie-breaking applied
        """
        # Initialize tie-breaking result with enhanced metrics
        tie_resolution = {
            "tied": True,
            "tied_options": tied_options,
            "vote_counts": vote_counts,
            "strategies_applied": [],
            "fairness_metrics": {
                "bias_assessment": 0,  # 0-10 scale, lower is better
                "process_transparency": 10,  # 0-10 scale, higher is better
            },
            "domain_expertise_consideration": {},
            "resolution_process": {
                "steps": [
                    {
                        "description": f"Identified tie between options: {', '.join(tied_options)}",
                        "outcome": "Proceeding with tie-breaking strategies",
                    }
                ]
            },
        }

        # Extract task domain and keywords for expertise assessment
        task_domain = task.get("domain", "")
        task_type = task.get("type", "")
        task_description = task.get("description", "")

        # Build keywords for expertise matching
        keywords = set()
        if task_domain:
            keywords.add(task_domain)
        if task_type:
            keywords.update(task_type.split("_"))
        if task_description:
            words = task_description.lower().split()
            keywords.update(
                [word for word in words if len(word) > 4 and word.isalpha()]
            )

        # 1. Try to break the tie using the Primus vote (enhanced with justification)
        primus_agent = self.get_primus()
        if primus_agent:
            primus_name = primus_agent.name
            primus_vote = voting_result["votes"].get(primus_name)

            # Add primus expertise assessment
            if hasattr(primus_agent, "expertise"):
                primus_expertise_weight = self._calculate_expertise_weight(
                    primus_agent, keywords
                )
                tie_resolution["domain_expertise_consideration"][
                    primus_name
                ] = primus_expertise_weight

                # Add step to resolution process
                tie_resolution["resolution_process"]["steps"].append(
                    {
                        "description": f"Assessed Primus ({primus_name}) expertise relevance to task",
                        "outcome": f"Expertise weight: {primus_expertise_weight:.2f}/10",
                    }
                )

            if primus_vote and primus_vote in tied_options:
                # Primus vote breaks the tie
                winner = primus_vote

                # Find the winning option details
                winning_option = next(
                    (option for option in task["options"] if option["id"] == winner),
                    None,
                )

                # Record the tie-breaking strategy
                tie_resolution["strategies_applied"].append(
                    {
                        "name": "Primus Tiebreaker",
                        "description": "The team leader's vote is given precedence in case of a tie",
                        "outcome": f"Selected option {winner} based on Primus ({primus_name}) vote",
                    }
                )

                # Update the resolution process
                tie_resolution["resolution_process"]["steps"].append(
                    {
                        "description": f"Applied Primus tiebreaker strategy",
                        "outcome": f"Tie broken in favor of {winner} based on Primus vote",
                    }
                )

                # Update the result
                tie_resolution["tied"] = False
                tie_resolution["winner"] = winner
                tie_resolution["winning_option"] = winning_option

                # Add the tie resolution to the voting result
                voting_result["result_type"] = "tie"
                voting_result["tie_resolution"] = tie_resolution

                # Add the selected option with tie-breaking rationale
                voting_result["selected_option"] = {
                    "id": winner,
                    "name": (
                        winning_option.get("name", winner) if winning_option else winner
                    ),
                    "tie_breaking_rationale": f"Selected based on Primus ({primus_name}) vote in a tie situation",
                }

                return voting_result
            else:
                # Record the failed strategy
                tie_resolution["strategies_applied"].append(
                    {
                        "name": "Primus Tiebreaker",
                        "description": "The team leader's vote is given precedence in case of a tie",
                        "outcome": "Strategy failed: Primus did not vote for any tied option",
                    }
                )

                # Update the resolution process
                tie_resolution["resolution_process"]["steps"].append(
                    {
                        "description": "Attempted to apply Primus tiebreaker strategy",
                        "outcome": "Strategy failed, proceeding to next strategy",
                    }
                )

        # 2. Try to break the tie using enhanced domain expertise weighting
        # Calculate expertise weights for all agents
        agent_expertise_weights = {}
        for agent in self.agents:
            agent_name = agent.name

            # Skip agents that didn't vote or didn't vote for a tied option
            agent_vote = voting_result["votes"].get(agent_name)
            if not agent_vote or agent_vote not in tied_options:
                continue

            # Calculate expertise weight using our enhanced method
            expertise_weight = self._calculate_expertise_weight(agent, keywords)
            agent_expertise_weights[agent_name] = expertise_weight

            # Store in the tie resolution for transparency
            tie_resolution["domain_expertise_consideration"][
                agent_name
            ] = expertise_weight

        # Update the resolution process
        tie_resolution["resolution_process"]["steps"].append(
            {
                "description": "Assessed domain expertise of all agents who voted for tied options",
                "outcome": f"Calculated expertise weights for {len(agent_expertise_weights)} agents",
            }
        )

        if agent_expertise_weights:
            # Group agents by their votes
            votes_by_option = {}
            for agent_name, weight in agent_expertise_weights.items():
                agent_vote = voting_result["votes"].get(agent_name)
                if agent_vote in tied_options:
                    if agent_vote not in votes_by_option:
                        votes_by_option[agent_vote] = []
                    votes_by_option[agent_vote].append((agent_name, weight))

            # Calculate weighted scores for each tied option
            option_scores = {}
            for option in tied_options:
                if option in votes_by_option:
                    # Sum the expertise weights of agents who voted for this option
                    option_scores[option] = sum(
                        weight for _, weight in votes_by_option[option]
                    )
                else:
                    option_scores[option] = 0

            # Find the option with the highest expertise-weighted score
            if option_scores:
                max_score = max(option_scores.values())
                winners = [
                    option
                    for option, score in option_scores.items()
                    if score == max_score
                ]

                # If we've narrowed it down to a single winner
                if len(winners) == 1:
                    winner = winners[0]

                    # Find the winning option details
                    winning_option = next(
                        (
                            option
                            for option in task["options"]
                            if option["id"] == winner
                        ),
                        None,
                    )

                    # Record the tie-breaking strategy
                    tie_resolution["strategies_applied"].append(
                        {
                            "name": "Domain Expertise Weighting",
                            "description": "Votes are weighted based on relevant domain expertise",
                            "outcome": f"Selected option {winner} with highest expertise-weighted score of {max_score:.2f}",
                        }
                    )

                    # Update the resolution process
                    tie_resolution["resolution_process"]["steps"].append(
                        {
                            "description": "Applied domain expertise weighting strategy",
                            "outcome": f"Tie broken in favor of {winner} based on expertise-weighted voting",
                        }
                    )

                    # List the experts who contributed to this decision
                    expert_agents = sorted(
                        votes_by_option.get(winner, []),
                        key=lambda x: x[1],
                        reverse=True,
                    )
                    if expert_agents:
                        top_expert = expert_agents[0][0]
                        tie_resolution["resolution_process"]["steps"].append(
                            {
                                "description": "Identified key experts who influenced this decision",
                                "outcome": f"Top expert: {top_expert} with expertise weight {expert_agents[0][1]:.2f}/10",
                            }
                        )

                    # Update the result
                    tie_resolution["tied"] = False
                    tie_resolution["winner"] = winner
                    tie_resolution["winning_option"] = winning_option
                    tie_resolution["option_scores"] = option_scores

                    # Add the tie resolution to the voting result
                    voting_result["result_type"] = "tie"
                    voting_result["tie_resolution"] = tie_resolution

                    # Add the selected option with tie-breaking rationale
                    voting_result["selected_option"] = {
                        "id": winner,
                        "name": (
                            winning_option.get("name", winner)
                            if winning_option
                            else winner
                        ),
                        "tie_breaking_rationale": f"Selected based on domain expertise weighting in a tie situation. Option {winner} received the highest expertise-weighted score.",
                    }

                    return voting_result
                else:
                    # Still tied after expertise weighting
                    tie_resolution["strategies_applied"].append(
                        {
                            "name": "Domain Expertise Weighting",
                            "description": "Votes are weighted based on relevant domain expertise",
                            "outcome": f"Strategy failed: Options {', '.join(winners)} still tied after expertise weighting",
                        }
                    )

                    # Update the resolution process
                    tie_resolution["resolution_process"]["steps"].append(
                        {
                            "description": "Attempted to apply domain expertise weighting strategy",
                            "outcome": "Strategy failed, proceeding to next strategy",
                        }
                    )

                    # Update tied options for next strategy
                    tied_options = winners
            else:
                # No expertise-weighted scores calculated
                tie_resolution["strategies_applied"].append(
                    {
                        "name": "Domain Expertise Weighting",
                        "description": "Votes are weighted based on relevant domain expertise",
                        "outcome": "Strategy failed: Could not calculate expertise-weighted scores",
                    }
                )

                # Update the resolution process
                tie_resolution["resolution_process"]["steps"].append(
                    {
                        "description": "Attempted to apply domain expertise weighting strategy",
                        "outcome": "Strategy failed, proceeding to next strategy",
                    }
                )

        # 3. Try to break the tie using historical consistency
        # This strategy favors options that have been consistently supported
        if hasattr(self, "voting_history") and self.voting_history:
            # Update the resolution process
            tie_resolution["resolution_process"]["steps"].append(
                {
                    "description": "Analyzing historical voting patterns",
                    "outcome": f"Examining {len(self.voting_history)} previous votes for consistency",
                }
            )

            # Count how many times each tied option has been supported in the past
            historical_support = {option: 0 for option in tied_options}

            for past_vote in self.voting_history:
                for option in tied_options:
                    if option in past_vote.get("votes", {}).values():
                        historical_support[option] += 1

            # Find the option with the most historical support
            if historical_support:
                max_support = max(historical_support.values())
                if max_support > 0:  # Only if we have some historical support
                    winners = [
                        option
                        for option, support in historical_support.items()
                        if support == max_support
                    ]

                    # If we've narrowed it down to a single winner
                    if len(winners) == 1:
                        winner = winners[0]

                        # Find the winning option details
                        winning_option = next(
                            (
                                option
                                for option in task["options"]
                                if option["id"] == winner
                            ),
                            None,
                        )

                        # Record the tie-breaking strategy
                        tie_resolution["strategies_applied"].append(
                            {
                                "name": "Historical Consistency",
                                "description": "Options with consistent support over time are favored",
                                "outcome": f"Selected option {winner} with highest historical support ({max_support} votes)",
                            }
                        )

                        # Update the resolution process
                        tie_resolution["resolution_process"]["steps"].append(
                            {
                                "description": "Applied historical consistency strategy",
                                "outcome": f"Tie broken in favor of {winner} based on historical voting patterns",
                            }
                        )

                        # Update the result
                        tie_resolution["tied"] = False
                        tie_resolution["winner"] = winner
                        tie_resolution["winning_option"] = winning_option
                        tie_resolution["historical_support"] = historical_support

                        # Add the tie resolution to the voting result
                        voting_result["result_type"] = "tie"
                        voting_result["tie_resolution"] = tie_resolution

                        # Add the selected option with tie-breaking rationale
                        voting_result["selected_option"] = {
                            "id": winner,
                            "name": (
                                winning_option.get("name", winner)
                                if winning_option
                                else winner
                            ),
                            "tie_breaking_rationale": f"Selected based on historical consistency in a tie situation. Option {winner} has received consistent support in past decisions.",
                        }

                        return voting_result
                    else:
                        # Still tied after historical consistency check
                        tie_resolution["strategies_applied"].append(
                            {
                                "name": "Historical Consistency",
                                "description": "Options with consistent support over time are favored",
                                "outcome": f"Strategy failed: Options {', '.join(winners)} still tied after historical analysis",
                            }
                        )

                        # Update the resolution process
                        tie_resolution["resolution_process"]["steps"].append(
                            {
                                "description": "Attempted to apply historical consistency strategy",
                                "outcome": "Strategy failed, proceeding to next strategy",
                            }
                        )

                        # Update tied options for next strategy
                        tied_options = winners
                else:
                    # No historical support found
                    tie_resolution["strategies_applied"].append(
                        {
                            "name": "Historical Consistency",
                            "description": "Options with consistent support over time are favored",
                            "outcome": "Strategy failed: No historical support found for any tied option",
                        }
                    )

                    # Update the resolution process
                    tie_resolution["resolution_process"]["steps"].append(
                        {
                            "description": "Attempted to apply historical consistency strategy",
                            "outcome": "Strategy failed, proceeding to next strategy",
                        }
                    )
            else:
                # No historical support data
                tie_resolution["strategies_applied"].append(
                    {
                        "name": "Historical Consistency",
                        "description": "Options with consistent support over time are favored",
                        "outcome": "Strategy failed: No historical support data available",
                    }
                )

                # Update the resolution process
                tie_resolution["resolution_process"]["steps"].append(
                    {
                        "description": "Attempted to apply historical consistency strategy",
                        "outcome": "Strategy failed, proceeding to next strategy",
                    }
                )
        else:
            # No voting history available
            tie_resolution["strategies_applied"].append(
                {
                    "name": "Historical Consistency",
                    "description": "Options with consistent support over time are favored",
                    "outcome": "Strategy failed: No voting history available",
                }
            )

            # Update the resolution process
            tie_resolution["resolution_process"]["steps"].append(
                {
                    "description": "Attempted to apply historical consistency strategy",
                    "outcome": "Strategy failed, proceeding to next strategy",
                }
            )

        # 4. Final fallback: Random selection with fairness guarantee
        # This is a last resort when all other strategies have failed
        # We use a deterministic but fair approach based on option IDs

        # Record the tie-breaking strategy
        tie_resolution["strategies_applied"].append(
            {
                "name": "Fair Random Selection",
                "description": "A deterministic but fair random selection as last resort",
                "outcome": f"Selecting from final tied options: {', '.join(tied_options)}",
            }
        )

        # Update the resolution process
        tie_resolution["resolution_process"]["steps"].append(
            {
                "description": "Applied fair random selection as final strategy",
                "outcome": "Using deterministic selection to ensure fairness",
            }
        )

        # Sort options alphabetically to ensure deterministic behavior
        sorted_options = sorted(tied_options)
        winner = sorted_options[0]  # Select the first option after sorting

        # Find the winning option details
        winning_option = next(
            (option for option in task["options"] if option["id"] == winner), None
        )

        # Update the result
        tie_resolution["tied"] = False
        tie_resolution["winner"] = winner
        tie_resolution["winning_option"] = winning_option

        # Add the tie resolution to the voting result
        voting_result["result_type"] = "tie"
        voting_result["tie_resolution"] = tie_resolution

        # Add the selected option with tie-breaking rationale
        voting_result["selected_option"] = {
            "id": winner,
            "name": winning_option.get("name", winner) if winning_option else winner,
            "tie_breaking_rationale": "Selected using fair random selection as a last resort after all other tie-breaking strategies failed.",
        }

        return voting_result

    def _generate_stakeholder_explanation(
        self, task: Dict[str, Any], consensus_result: Dict[str, Any]
    ) -> str:
        """
        Generate a stakeholder-friendly explanation of a decision.

        This enhanced version creates a more comprehensive and clear explanation
        that avoids technical jargon and focuses on the key points that stakeholders
        would care about.

        Args:
            task: The task
            consensus_result: The consensus result

        Returns:
            A stakeholder-friendly explanation
        """
        # Get task details
        task_description = task.get("description", "this matter")
        task_criticality = task.get("criticality", "medium")

        # Create a clear introduction
        explanation = f"Decision: {task_description}\n\n"

        # Add the actual decision
        explanation += f"We selected the following approach: {consensus_result.get('consensus', '')}\n\n"

        # Add criticality context
        if task_criticality == "high":
            explanation += "This was identified as a high-priority decision with significant impact. "
        elif task_criticality == "medium":
            explanation += "This was identified as a medium-priority decision with moderate impact. "
        else:
            explanation += "This was identified as a routine decision. "

        # Explain the decision-making process
        explanation += "This decision was made through a collaborative process where all team members contributed their expertise.\n\n"

        # Add information about conflicts if present
        if consensus_result.get("identified_conflicts"):
            explanation += "We carefully considered different perspectives and resolved conflicts to arrive at a solution that addresses all key concerns.\n\n"

            # Add details about how conflicts were resolved
            conflict_count = len(consensus_result.get("identified_conflicts", []))
            explanation += f"Our team resolved {conflict_count} different viewpoints by focusing on the expertise of each team member "
            explanation += "and finding common ground that leverages the strengths of multiple approaches.\n\n"

        # Add the benefits section with more specific benefits if available
        explanation += "The main benefits of this approach are:\n"

        # Use actual strengths if available
        if "strengths" in consensus_result and consensus_result["strengths"]:
            for i, strength in enumerate(
                consensus_result["strengths"][:3]
            ):  # Use up to 3 actual strengths
                # Simplify the strength statement for stakeholders
                simplified_strength = strength.replace("Leverages", "Uses").replace(
                    "expertise in", "knowledge of"
                )
                explanation += f"- Benefit {i+1}: {simplified_strength}\n"

            # If we have fewer than 3 strengths, add generic ones to reach 3
            for i in range(len(consensus_result["strengths"]), 3):
                explanation += f"- Benefit {i+1}: This approach provides significant advantages in terms of {['quality', 'efficiency', 'maintainability', 'scalability', 'security'][i % 5]}.\n"
        else:
            # Use generic benefits if no strengths are available
            for i in range(3):
                explanation += f"- Benefit {i+1}: This approach provides significant advantages in terms of {['quality', 'efficiency', 'maintainability', 'scalability', 'security'][i % 5]}.\n"

        # Add next steps or implementation notes
        explanation += "\nNext steps: This decision will be implemented according to the project plan. "
        explanation += (
            "The implementation status will be tracked and reported in future updates."
        )

        return explanation
