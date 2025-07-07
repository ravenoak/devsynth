"""
Task management functionality for Collaborative WSDE Team.

This module provides task management methods for the CollaborativeWSDETeam class,
including subtask handling, progress tracking, and task reassignment.

This is part of an effort to break up the monolithic wsde_team_extended.py
into smaller, more focused modules.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid

from devsynth.domain.models.wsde_facade import WSDETeam


class TaskManagementMixin:
    """
    Mixin class providing task management functionality for CollaborativeWSDETeam.

    This mixin adds methods for handling subtasks, tracking progress, and
    reassigning tasks based on progress.
    """

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task by breaking it down into subtasks and delegating them.

        Args:
            task: The task to process

        Returns:
            The processed task with results
        """
        # Ensure task has an ID
        if "id" not in task:
            task["id"] = str(uuid.uuid4())

        # Log the task processing
        self.logger.info(f"Processing task {task['id']}: {task.get('title', 'Untitled')}")

        # Check if task has subtasks defined
        if "subtasks" in task and task["subtasks"]:
            subtasks = task["subtasks"]
        else:
            # Generate subtasks based on task requirements
            subtasks = self._generate_subtasks(task)
            task["subtasks"] = subtasks

        # Associate subtasks with main task
        self.associate_subtasks(task, subtasks)

        # Delegate subtasks to team members
        delegation_results = self.delegate_subtasks(subtasks)
        task["delegation_results"] = delegation_results

        # Track progress on subtasks
        self._track_subtask_progress(task["id"])

        # Reassign subtasks if needed based on progress
        if any(progress < 0.5 for progress in self.subtask_progress.values()):
            self.reassign_subtasks_based_on_progress(subtasks)

        # Collect results from completed subtasks
        results = self._collect_subtask_results(task["id"])
        task["results"] = results

        # Update contribution metrics
        self._update_contribution_metrics(task["id"])

        return task

    def _generate_subtasks(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate subtasks based on task requirements.

        Args:
            task: The main task

        Returns:
            List of generated subtasks
        """
        subtasks = []

        # Extract requirements from task
        requirements = task.get("requirements", [])
        if not requirements and "description" in task:
            # Try to extract requirements from description
            description = task["description"]
            requirements = [line.strip("- ") for line in description.split("\n") 
                           if line.strip().startswith("-")]

        # Create a subtask for each requirement
        for i, req in enumerate(requirements):
            subtask = {
                "id": f"{task['id']}_subtask_{i}",
                "title": f"Subtask {i+1}: {req[:50]}...",
                "description": req,
                "parent_task_id": task["id"],
                "status": "pending",
                "priority": "medium",
                "assigned_to": None
            }
            subtasks.append(subtask)

        return subtasks

    def associate_subtasks(self, main_task: Dict[str, Any], subtasks: List[Dict[str, Any]]) -> None:
        """
        Associate subtasks with a main task.

        Args:
            main_task: The main task
            subtasks: List of subtasks to associate
        """
        task_id = main_task["id"]

        # Initialize subtasks dictionary for this task if it doesn't exist
        if task_id not in self.subtasks:
            self.subtasks[task_id] = []

        # Add subtasks to the dictionary
        for subtask in subtasks:
            # Ensure subtask has an ID
            if "id" not in subtask:
                subtask["id"] = f"{task_id}_subtask_{len(self.subtasks[task_id])}"

            # Ensure subtask has a reference to parent task
            subtask["parent_task_id"] = task_id

            # Add subtask to the list
            self.subtasks[task_id].append(subtask)

        self.logger.debug(f"Associated {len(subtasks)} subtasks with task {task_id}")

    def delegate_subtasks(self, subtasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Delegate subtasks to team members based on expertise.

        Args:
            subtasks: List of subtasks to delegate

        Returns:
            List of delegation results
        """
        delegation_results = []

        for subtask in subtasks:
            # Find the best agent for this subtask
            best_agent = None
            best_score = -1

            for agent in self.agents:
                # Calculate expertise score for this agent and subtask
                score = self._calculate_expertise_score(agent, subtask)

                # Update best agent if this one has a higher score
                if score > best_score:
                    best_score = score
                    best_agent = agent

            # Assign subtask to the best agent
            if best_agent:
                subtask["assigned_to"] = best_agent.name
                subtask["expertise_score"] = best_score
                subtask["status"] = "assigned"

                # Log the delegation
                self.logger.info(f"Delegated subtask {subtask['id']} to {best_agent.name} (score: {best_score:.2f})")

                # Send a message to the agent
                self.send_message(
                    sender="system",
                    recipients=[best_agent.name],
                    message_type="task_assignment",
                    subject=f"Subtask Assignment: {subtask['title']}",
                    content=subtask
                )

                # Add to delegation results
                delegation_results.append({
                    "subtask_id": subtask["id"],
                    "assigned_to": best_agent.name,
                    "expertise_score": best_score,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # No suitable agent found
                subtask["status"] = "unassigned"
                self.logger.warning(f"No suitable agent found for subtask {subtask['id']}")

                # Add to delegation results
                delegation_results.append({
                    "subtask_id": subtask["id"],
                    "assigned_to": None,
                    "expertise_score": 0,
                    "timestamp": datetime.now().isoformat()
                })

        return delegation_results

    def update_subtask_progress(self, subtask_id: str, progress: float) -> None:
        """
        Update the progress of a subtask.

        Args:
            subtask_id: ID of the subtask
            progress: Progress value between 0 and 1
        """
        # Validate progress value
        if not 0 <= progress <= 1:
            raise ValueError("Progress must be between 0 and 1")

        # Update progress
        self.subtask_progress[subtask_id] = progress

        # Log the update
        self.logger.debug(f"Updated progress for subtask {subtask_id}: {progress:.2f}")

        # Find the subtask and update its status
        for task_id, subtasks in self.subtasks.items():
            for subtask in subtasks:
                if subtask["id"] == subtask_id:
                    if progress >= 1.0:
                        subtask["status"] = "completed"
                    elif progress > 0:
                        subtask["status"] = "in_progress"
                    else:
                        subtask["status"] = "assigned"

                    # Update the subtask's progress field
                    subtask["progress"] = progress
                    return

    def reassign_subtasks_based_on_progress(self, subtasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reassign subtasks based on progress and agent availability.

        Args:
            subtasks: List of subtasks to potentially reassign

        Returns:
            List of reassignment results
        """
        reassignment_results = []

        # Get current agent workloads
        agent_workloads = self._calculate_agent_workloads()

        # Identify subtasks with low progress
        low_progress_subtasks = []
        for subtask in subtasks:
            subtask_id = subtask["id"]
            if subtask_id in self.subtask_progress and self.subtask_progress[subtask_id] < 0.3:
                if subtask["status"] != "completed" and "assigned_to" in subtask:
                    low_progress_subtasks.append(subtask)

        # Sort by priority and then by progress (lowest first)
        low_progress_subtasks.sort(
            key=lambda s: (
                {"high": 0, "medium": 1, "low": 2}.get(s.get("priority", "medium"), 1),
                self.subtask_progress.get(s["id"], 0)
            )
        )

        # Reassign subtasks with low progress
        for subtask in low_progress_subtasks:
            current_assignee = subtask["assigned_to"]

            # Find a better agent for this subtask
            best_agent = None
            best_score = -1

            for agent in self.agents:
                # Skip the current assignee
                if agent.name == current_assignee:
                    continue

                # Calculate expertise score for this agent and subtask
                expertise_score = self._calculate_expertise_score(agent, subtask)

                # Adjust score based on agent workload
                workload_factor = 1.0 - (agent_workloads.get(agent.name, 0) / max(len(subtasks), 1))
                adjusted_score = expertise_score * workload_factor

                # Update best agent if this one has a higher score
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_agent = agent

            # Reassign subtask if a better agent was found
            if best_agent and best_score > self.subtask_progress.get(subtask["id"], 0) * 1.5:
                # Update subtask assignment
                old_assignee = subtask["assigned_to"]
                subtask["assigned_to"] = best_agent.name
                subtask["expertise_score"] = best_score
                subtask["reassigned"] = True
                subtask["previous_assignee"] = old_assignee

                # Log the reassignment
                self.logger.info(
                    f"Reassigned subtask {subtask['id']} from {old_assignee} to {best_agent.name} "
                    f"(new score: {best_score:.2f}, progress: {self.subtask_progress.get(subtask['id'], 0):.2f})"
                )

                # Send messages to both agents
                self.send_message(
                    sender="system",
                    recipients=[best_agent.name],
                    message_type="task_assignment",
                    subject=f"Subtask Reassignment: {subtask['title']}",
                    content=subtask
                )

                self.send_message(
                    sender="system",
                    recipients=[old_assignee],
                    message_type="task_reassignment",
                    subject=f"Subtask Reassigned: {subtask['title']}",
                    content={"subtask_id": subtask["id"], "new_assignee": best_agent.name}
                )

                # Add to reassignment results
                reassignment_results.append({
                    "subtask_id": subtask["id"],
                    "previous_assignee": old_assignee,
                    "new_assignee": best_agent.name,
                    "expertise_score": best_score,
                    "progress_at_reassignment": self.subtask_progress.get(subtask["id"], 0),
                    "timestamp": datetime.now().isoformat()
                })

                # Update agent workloads
                agent_workloads[old_assignee] = max(0, agent_workloads.get(old_assignee, 0) - 1)
                agent_workloads[best_agent.name] = agent_workloads.get(best_agent.name, 0) + 1

        return reassignment_results

    def _calculate_agent_workloads(self) -> Dict[str, int]:
        """
        Calculate the current workload for each agent.

        Returns:
            Dictionary mapping agent names to their workload counts
        """
        workloads = {}

        # Count assigned subtasks for each agent
        for task_subtasks in self.subtasks.values():
            for subtask in task_subtasks:
                if "assigned_to" in subtask and subtask["status"] != "completed":
                    assignee = subtask["assigned_to"]
                    workloads[assignee] = workloads.get(assignee, 0) + 1

        return workloads

    def _track_subtask_progress(self, task_id: str) -> None:
        """
        Track progress on subtasks for a given task.

        Args:
            task_id: ID of the main task
        """
        if task_id not in self.subtasks:
            return

        # Update progress for each subtask
        for subtask in self.subtasks[task_id]:
            subtask_id = subtask["id"]

            # Skip if progress is already tracked and subtask is completed
            if subtask_id in self.subtask_progress and self.subtask_progress[subtask_id] >= 1.0:
                continue

            # Get messages related to this subtask
            messages = self.get_messages(
                filters={"metadata.subtask_id": subtask_id, "type": "progress_update"}
            )

            if messages:
                # Use the latest progress update
                latest_message = max(messages, key=lambda m: m["timestamp"])
                progress = latest_message["content"].get("progress", 0)
                self.update_subtask_progress(subtask_id, progress)
            elif "progress" in subtask:
                # Use progress from subtask if available
                self.update_subtask_progress(subtask_id, subtask["progress"])

    def _collect_subtask_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Collect results from completed subtasks.

        Args:
            task_id: ID of the main task

        Returns:
            List of subtask results
        """
        results = []

        if task_id not in self.subtasks:
            return results

        for subtask in self.subtasks[task_id]:
            subtask_id = subtask["id"]

            # Get result messages for this subtask
            messages = self.get_messages(
                filters={"metadata.subtask_id": subtask_id, "type": "subtask_result"}
            )

            if messages:
                # Use the latest result
                latest_message = max(messages, key=lambda m: m["timestamp"])
                result = {
                    "subtask_id": subtask_id,
                    "title": subtask.get("title", ""),
                    "assigned_to": subtask.get("assigned_to", ""),
                    "result": latest_message["content"],
                    "timestamp": latest_message["timestamp"].isoformat() 
                        if isinstance(latest_message["timestamp"], datetime) 
                        else latest_message["timestamp"]
                }
                results.append(result)

        return results

    def _update_contribution_metrics(self, task_id: str) -> None:
        """
        Update contribution metrics for agents based on task completion.

        Args:
            task_id: ID of the main task
        """
        if task_id not in self.subtasks:
            return

        # Initialize metrics for this task if they don't exist
        if task_id not in self.contribution_metrics:
            self.contribution_metrics[task_id] = {}

        # Update metrics for each agent
        for subtask in self.subtasks[task_id]:
            if "assigned_to" not in subtask:
                continue

            agent_name = subtask["assigned_to"]
            subtask_id = subtask["id"]

            # Initialize agent metrics if they don't exist
            if agent_name not in self.contribution_metrics[task_id]:
                self.contribution_metrics[task_id][agent_name] = {
                    "assigned_subtasks": 0,
                    "completed_subtasks": 0,
                    "total_progress": 0,
                    "average_progress": 0
                }

            # Update metrics
            metrics = self.contribution_metrics[task_id][agent_name]
            metrics["assigned_subtasks"] += 1

            if subtask_id in self.subtask_progress:
                progress = self.subtask_progress[subtask_id]
                metrics["total_progress"] += progress

                if progress >= 1.0:
                    metrics["completed_subtasks"] += 1

            # Calculate average progress
            metrics["average_progress"] = metrics["total_progress"] / metrics["assigned_subtasks"]

    def get_contribution_metrics(self, task_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get contribution metrics for a specific task.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary mapping agent names to their contribution metrics
        """
        return self.contribution_metrics.get(task_id, {})

    def update_task_requirements(self, updated_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update task requirements and adjust subtasks accordingly.

        Args:
            updated_task: The updated task with new requirements

        Returns:
            The updated task with adjusted subtasks
        """
        task_id = updated_task["id"]

        # Check if task exists in subtasks dictionary
        if task_id not in self.subtasks:
            # If not, treat it as a new task
            return self.process_task(updated_task)

        # Get existing subtasks
        existing_subtasks = self.subtasks[task_id]

        # Get new requirements
        new_requirements = updated_task.get("requirements", [])
        if not new_requirements and "description" in updated_task:
            # Try to extract requirements from description
            description = updated_task["description"]
            new_requirements = [line.strip("- ") for line in description.split("\n") 
                               if line.strip().startswith("-")]

        # Map existing subtasks to their requirements
        existing_req_map = {}
        for subtask in existing_subtasks:
            req = subtask.get("description", "")
            existing_req_map[req] = subtask

        # Create updated subtasks list
        updated_subtasks = []

        # Process each new requirement
        for i, req in enumerate(new_requirements):
            if req in existing_req_map:
                # Requirement exists, keep the existing subtask
                updated_subtasks.append(existing_req_map[req])
            else:
                # New requirement, create a new subtask
                new_subtask = {
                    "id": f"{task_id}_subtask_{len(existing_subtasks) + i}",
                    "title": f"Subtask {len(updated_subtasks) + 1}: {req[:50]}...",
                    "description": req,
                    "parent_task_id": task_id,
                    "status": "pending",
                    "priority": "medium",
                    "assigned_to": None
                }
                updated_subtasks.append(new_subtask)

        # Update the task's subtasks
        updated_task["subtasks"] = updated_subtasks
        self.subtasks[task_id] = updated_subtasks

        # Delegate any new subtasks
        new_subtasks = [s for s in updated_subtasks if s["status"] == "pending"]
        if new_subtasks:
            delegation_results = self.delegate_subtasks(new_subtasks)

            # Add to existing delegation results if they exist
            if "delegation_results" in updated_task:
                updated_task["delegation_results"].extend(delegation_results)
            else:
                updated_task["delegation_results"] = delegation_results

        return updated_task
