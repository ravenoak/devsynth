"""Task management functionality for Collaborative WSDE Team."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
from collections.abc import Sequence

from .structures import (
    SubtaskSpec,
    TaskDelegationResult,
    TaskInput,
    TaskManagementContext,
    TaskReassignmentResult,
    TaskSpec,
)


def _ensure_task_spec(task: TaskInput) -> TaskSpec:
    """Normalize arbitrary task input into a :class:`TaskSpec`."""

    if isinstance(task, TaskSpec):
        return task

    payload = dict(task)
    payload.setdefault("id", str(uuid.uuid4()))
    return TaskSpec.from_mapping(payload)


class TaskManagementMixin:
    """
    Mixin class providing task management functionality for CollaborativeWSDETeam.

    This mixin adds methods for handling subtasks, tracking progress, and
    reassigning tasks based on progress.
    """

    def process_task(self, task: TaskInput) -> dict[str, Any]:
        """Process a task by breaking it down into subtasks and delegating them."""

        context = cast(TaskManagementContext, self)
        task_spec = _ensure_task_spec(task)

        context.logger.info(
            "Processing task %s: %s",
            task_spec.id,
            task_spec.title or "Untitled",
        )

        if hasattr(self, "dynamic_role_reassignment"):
            self.dynamic_role_reassignment(task_spec.to_payload())

        if task_spec.subtasks:
            subtasks = task_spec.subtasks
        else:
            subtasks = self._generate_subtasks(task_spec)
            task_spec.subtasks = subtasks

        self.associate_subtasks(task_spec, subtasks)

        delegation_results = self.delegate_subtasks(subtasks)

        self._track_subtask_progress(task_spec.id)

        if any(
            context.subtask_progress.get(subtask.id, 0.0) < 0.5 for subtask in subtasks
        ):
            reassignments = self.reassign_subtasks_based_on_progress(subtasks)
            if reassignments:
                task_spec.metadata.setdefault("reassignments", []).extend(
                    [result.to_payload() for result in reassignments]
                )

        results = self._collect_subtask_results(task_spec.id)
        payload: dict[str, Any] = task_spec.to_payload()
        payload["delegation_results"] = [
            result.to_payload() for result in delegation_results
        ]
        payload["results"] = results

        self._update_contribution_metrics(task_spec.id)

        return payload

    def _generate_subtasks(self, task: TaskSpec) -> list[SubtaskSpec]:
        """Generate subtasks based on task requirements."""

        subtasks: list[SubtaskSpec] = []

        requirements = list(task.requirements)
        if not requirements and task.description:
            description = task.description
            requirements = [
                line.strip("- ")
                for line in description.split("\n")
                if line.strip().startswith("-")
            ]
            task.requirements = requirements

        for index, requirement in enumerate(requirements):
            subtask_id = f"{task.id}_subtask_{index}"
            subtasks.append(
                SubtaskSpec(
                    id=subtask_id,
                    title=f"Subtask {index + 1}: {requirement[:50]}...",
                    description=requirement,
                    parent_task_id=task.id,
                )
            )

        return subtasks

    def associate_subtasks(
        self, main_task: TaskSpec, subtasks: Sequence[SubtaskSpec]
    ) -> None:
        """Associate subtasks with a main task."""

        context = cast(TaskManagementContext, self)
        task_id = main_task.id
        prepared_subtasks: list[SubtaskSpec] = []
        for index, subtask in enumerate(subtasks):
            if not subtask.id:
                subtask.id = f"{task_id}_subtask_{index}"
            subtask.parent_task_id = task_id
            prepared_subtasks.append(subtask)

        context.subtasks[task_id] = prepared_subtasks
        main_task.subtasks = list(prepared_subtasks)

        context.logger.debug(
            "Associated %d subtasks with task %s", len(prepared_subtasks), task_id
        )

    def delegate_subtasks(
        self, subtasks: Sequence[SubtaskSpec]
    ) -> list[TaskDelegationResult]:
        """Delegate subtasks to team members based on expertise."""

        context = cast(TaskManagementContext, self)
        delegation_results: list[TaskDelegationResult] = []

        for subtask in subtasks:
            best_agent = None
            best_score = -1.0

            for agent in context.agents:
                score = context._calculate_expertise_score(agent, subtask.to_payload())
                if score > best_score:
                    best_score = float(score)
                    best_agent = agent

            if best_agent:
                subtask.assigned_to = best_agent.name
                subtask.expertise_score = best_score
                subtask.status = "assigned"

                context.logger.info(
                    "Delegated subtask %s to %s (score: %.2f)",
                    subtask.id,
                    best_agent.name,
                    best_score,
                )

                context.send_message(
                    sender="system",
                    recipients=[best_agent.name],
                    message_type="task_assignment",
                    subject=f"Subtask Assignment: {subtask.title}",
                    content=subtask.to_payload(),
                )

                delegation_results.append(
                    TaskDelegationResult(
                        subtask_id=subtask.id,
                        assigned_to=best_agent.name,
                        expertise_score=best_score,
                        timestamp=datetime.now().isoformat(),
                    )
                )
            else:
                subtask.status = "unassigned"
                context.logger.warning(
                    "No suitable agent found for subtask %s", subtask.id
                )

                delegation_results.append(
                    TaskDelegationResult(
                        subtask_id=subtask.id,
                        assigned_to=None,
                        expertise_score=0.0,
                        timestamp=datetime.now().isoformat(),
                    )
                )

        return delegation_results

    def update_subtask_progress(self, subtask_id: str, progress: float) -> None:
        """Update the progress of a subtask."""

        context = cast(TaskManagementContext, self)
        if not 0.0 <= progress <= 1.0:
            raise ValueError("Progress must be between 0 and 1")

        context.subtask_progress[subtask_id] = progress
        context.logger.debug(
            "Updated progress for subtask %s: %.2f", subtask_id, progress
        )

        for task_subtasks in context.subtasks.values():
            for subtask in task_subtasks:
                if subtask.id == subtask_id:
                    if progress >= 1.0:
                        subtask.status = "completed"
                    elif progress > 0:
                        subtask.status = "in_progress"
                    else:
                        subtask.status = (
                            "assigned" if subtask.assigned_to else "pending"
                        )

                    subtask.progress = progress
                    return

    def reassign_subtasks_based_on_progress(
        self, subtasks: Sequence[SubtaskSpec]
    ) -> list[TaskReassignmentResult]:
        """Reassign subtasks based on progress and agent availability."""

        context = cast(TaskManagementContext, self)
        reassignment_results: list[TaskReassignmentResult] = []
        agent_workloads = self._calculate_agent_workloads()

        low_progress_subtasks: list[SubtaskSpec] = []
        for subtask in subtasks:
            progress = context.subtask_progress.get(subtask.id, 0.0)
            if progress < 0.3 and subtask.status != "completed" and subtask.assigned_to:
                low_progress_subtasks.append(subtask)

        priority_order = {"high": 0, "medium": 1, "low": 2}
        low_progress_subtasks.sort(
            key=lambda sub: (
                priority_order.get(sub.priority, 1),
                context.subtask_progress.get(sub.id, 0.0),
            )
        )

        for subtask in low_progress_subtasks:
            current_assignee = subtask.assigned_to
            if not current_assignee:
                continue

            best_agent = None
            best_score = -1.0
            for agent in context.agents:
                if agent.name == current_assignee:
                    continue

                expertise_score = float(
                    context._calculate_expertise_score(agent, subtask.to_payload())
                )
                workload_factor = 1.0 - (
                    agent_workloads.get(agent.name, 0) / max(len(subtasks), 1)
                )
                adjusted_score = expertise_score * workload_factor

                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_agent = agent

            current_progress = context.subtask_progress.get(subtask.id, 0.0)
            if best_agent and best_score > current_progress * 1.5:
                old_assignee = current_assignee
                subtask.assigned_to = best_agent.name
                subtask.expertise_score = best_score
                subtask.reassigned = True
                subtask.previous_assignee = old_assignee

                context.logger.info(
                    "Reassigned subtask %s from %s to %s (score: %.2f, progress: %.2f)",
                    subtask.id,
                    old_assignee,
                    best_agent.name,
                    best_score,
                    current_progress,
                )

                context.send_message(
                    sender="system",
                    recipients=[best_agent.name],
                    message_type="task_assignment",
                    subject=f"Subtask Reassignment: {subtask.title}",
                    content=subtask.to_payload(),
                )

                context.send_message(
                    sender="system",
                    recipients=[old_assignee],
                    message_type="task_reassignment",
                    subject=f"Subtask Reassigned: {subtask.title}",
                    content={
                        "subtask_id": subtask.id,
                        "new_assignee": best_agent.name,
                    },
                )

                reassignment_results.append(
                    TaskReassignmentResult(
                        subtask_id=subtask.id,
                        previous_assignee=old_assignee,
                        new_assignee=best_agent.name,
                        expertise_score=best_score,
                        progress_at_reassignment=current_progress,
                        timestamp=datetime.now().isoformat(),
                    )
                )

                agent_workloads[old_assignee] = max(
                    0, agent_workloads.get(old_assignee, 0) - 1
                )
                agent_workloads[best_agent.name] = (
                    agent_workloads.get(best_agent.name, 0) + 1
                )

        return reassignment_results

    def _calculate_agent_workloads(self) -> dict[str, int]:
        """Calculate the current workload for each agent."""

        context = cast(TaskManagementContext, self)
        workloads: dict[str, int] = {}
        for task_subtasks in context.subtasks.values():
            for subtask in task_subtasks:
                if subtask.assigned_to and subtask.status != "completed":
                    workloads[subtask.assigned_to] = (
                        workloads.get(subtask.assigned_to, 0) + 1
                    )

        return workloads

    def _track_subtask_progress(self, task_id: str) -> None:
        """Track progress on subtasks for a given task."""

        context = cast(TaskManagementContext, self)
        if task_id not in context.subtasks:
            return

        for subtask in context.subtasks[task_id]:
            if (
                subtask.id in context.subtask_progress
                and context.subtask_progress[subtask.id] >= 1.0
            ):
                continue

            messages = context.get_messages(
                filters={
                    "metadata.subtask_id": subtask.id,
                    "type": "progress_update",
                }
            )

            if messages:
                latest_message = max(messages, key=lambda message: message["timestamp"])
                progress = latest_message["content"].get("progress", 0)
                self.update_subtask_progress(subtask.id, progress)
            elif subtask.progress:
                self.update_subtask_progress(subtask.id, subtask.progress)

    def _collect_subtask_results(self, task_id: str) -> list[dict[str, Any]]:
        """Collect results from completed subtasks."""

        context = cast(TaskManagementContext, self)
        results: list[dict[str, Any]] = []

        if task_id not in context.subtasks:
            return results

        for subtask in context.subtasks[task_id]:
            messages = context.get_messages(
                filters={
                    "metadata.subtask_id": subtask.id,
                    "type": "subtask_result",
                }
            )

            if messages:
                latest_message = max(messages, key=lambda message: message["timestamp"])
                timestamp = latest_message["timestamp"]
                if isinstance(timestamp, datetime):
                    timestamp_str = timestamp.isoformat()
                else:
                    timestamp_str = timestamp

                results.append(
                    {
                        "subtask_id": subtask.id,
                        "title": subtask.title,
                        "assigned_to": subtask.assigned_to or "",
                        "result": latest_message["content"],
                        "timestamp": timestamp_str,
                    }
                )

        return results

    def _update_contribution_metrics(self, task_id: str) -> None:
        """Update contribution metrics for agents based on task completion."""

        context = cast(TaskManagementContext, self)
        if task_id not in context.subtasks:
            return

        task_metrics = context.contribution_metrics.setdefault(task_id, {})
        for subtask in context.subtasks[task_id]:
            if not subtask.assigned_to:
                continue

            agent_metrics = task_metrics.setdefault(
                subtask.assigned_to,
                {
                    "assigned_subtasks": 0,
                    "completed_subtasks": 0,
                    "total_progress": 0.0,
                    "average_progress": 0.0,
                },
            )

            agent_metrics["assigned_subtasks"] += 1
            progress = context.subtask_progress.get(subtask.id, subtask.progress)
            agent_metrics["total_progress"] += progress
            if progress >= 1.0:
                agent_metrics["completed_subtasks"] += 1
            agent_metrics["average_progress"] = (
                agent_metrics["total_progress"] / agent_metrics["assigned_subtasks"]
            )

    def get_contribution_metrics(self, task_id: str) -> dict[str, dict[str, Any]]:
        """
        Get contribution metrics for a specific task.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary mapping agent names to their contribution metrics
        """
        context = cast(TaskManagementContext, self)
        metrics = context.contribution_metrics.get(task_id)
        if metrics is None:
            return {}
        return {agent: dict(values) for agent, values in metrics.items()}

    def update_task_requirements(self, updated_task: TaskInput) -> dict[str, Any]:
        """Update task requirements and adjust subtasks accordingly."""

        context = cast(TaskManagementContext, self)
        task_spec = _ensure_task_spec(updated_task)
        task_id = task_spec.id

        if task_id not in context.subtasks:
            return TaskManagementMixin.process_task(self, task_spec)

        existing_subtasks = context.subtasks[task_id]
        requirement_map = {
            subtask.description: subtask for subtask in existing_subtasks
        }

        new_requirements = list(task_spec.requirements)
        if not new_requirements and task_spec.description:
            description = task_spec.description
            new_requirements = [
                line.strip("- ")
                for line in description.split("\n")
                if line.strip().startswith("-")
            ]
            task_spec.requirements = new_requirements

        updated_subtasks: list[SubtaskSpec] = []
        for index, requirement in enumerate(new_requirements):
            if requirement in requirement_map:
                updated_subtasks.append(requirement_map[requirement])
            else:
                updated_subtasks.append(
                    SubtaskSpec(
                        id=f"{task_id}_subtask_{len(existing_subtasks) + index}",
                        title=f"Subtask {len(updated_subtasks) + 1}: {requirement[:50]}...",
                        description=requirement,
                        parent_task_id=task_id,
                    )
                )

        task_spec.subtasks = updated_subtasks
        context.subtasks[task_id] = updated_subtasks

        new_pending = [sub for sub in updated_subtasks if sub.status == "pending"]
        delegation_results: list[TaskDelegationResult] = []
        if new_pending:
            delegation_results = self.delegate_subtasks(new_pending)

        payload: dict[str, Any] = task_spec.to_payload()
        if delegation_results:
            payload.setdefault("delegation_results", []).extend(
                result.to_payload() for result in delegation_results
            )
        return payload
