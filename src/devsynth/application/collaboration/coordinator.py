
"""
Agent coordinator implementation for managing agent collaboration.
"""

import logging
from typing import Any, Dict, List, Optional
from ...domain.interfaces.agent import Agent, AgentCoordinator
from ...domain.models.wsde import WSDATeam, WSDE
from .exceptions import (

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError
    CollaborationError, 
    AgentExecutionError, 
    ConsensusError, 
    RoleAssignmentError,
    TeamConfigurationError
)

logger = logging.getLogger(__name__)

class AgentCoordinatorImpl(AgentCoordinator):
    """Implementation of the AgentCoordinator interface."""
    
    def __init__(self):
        """Initialize the agent coordinator."""
        self.agents: List[Agent] = []
        self.team = WSDATeam()
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the coordinator and team."""
        self.agents.append(agent)
        self.team.add_agent(agent)
    
    def delegate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate a task to the appropriate agent(s).
        
        Args:
            task: A dictionary containing task details.
                If 'agent_type' is specified, the task is delegated to an agent of that type.
                If 'team_task' is True, the task is delegated to the entire team.
                
        Returns:
            A dictionary containing the task results.
            
        Raises:
            CollaborationError: If there's an error during task delegation.
        """
        try:
            # Check if this is a team task
            if task.get("team_task", False):
                return self._handle_team_task(task)
            
            # Otherwise, delegate to a specific agent type
            agent_type = task.get("agent_type")
            if not agent_type:
                raise ValidationError(f"Either 'team_task' must be True or 'agent_type' must be specified")
            
            return self._delegate_to_agent_type(agent_type, task)
        
        except Exception as e:
            if isinstance(e, CollaborationError):
                raise
            
            logger.error(f"Error delegating task: {str(e)}")
            raise CollaborationError(f"Failed to delegate task: {str(e)}")
    
    def _delegate_to_agent_type(self, agent_type: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a task to an agent of a specific type."""
        for agent in self.agents:
            if agent.agent_type == agent_type:
                try:
                    return agent.process(task)
                except Exception as e:
                    logger.error(f"Agent {agent.name} failed to process task: {str(e)}")
                    raise AgentExecutionError(
                        f"Agent {agent.name} failed to process task: {str(e)}",
                        agent_id=getattr(agent, 'name', None),
                        task=task
                    )
        
        raise ValidationError(f"No agent found with type: {agent_type}")
    
    def _handle_team_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a task that requires team collaboration."""
        if not self.agents:
            raise TeamConfigurationError("No agents available in the team")
        
        # Assign roles to team members
        self.team.assign_roles()
        
        # Get the current Primus agent
        primus = self.team.get_primus()
        if not primus:
            raise RoleAssignmentError("Failed to assign Primus role")
        
        # First, let the Designer plan the approach
        designer = self.team.get_designer()
        if designer:
            try:
                design_result = designer.process({
                    **task,
                    "role": "Designer",
                    "action": "plan"
                })
                logger.info(f"Designer {designer.name} created plan")
            except Exception as e:
                logger.error(f"Designer {designer.name} failed: {str(e)}")
                raise AgentExecutionError(
                    f"Designer {designer.name} failed: {str(e)}",
                    agent_id=getattr(designer, 'name', None),
                    role="Designer",
                    task=task
                )
        else:
            design_result = {}
        
        # Then, let the Worker implement the solution
        worker = self.team.get_worker()
        if worker:
            try:
                work_result = worker.process({
                    **task,
                    "role": "Worker",
                    "action": "implement",
                    "design": design_result
                })
                logger.info(f"Worker {worker.name} completed implementation")
            except Exception as e:
                logger.error(f"Worker {worker.name} failed: {str(e)}")
                raise AgentExecutionError(
                    f"Worker {worker.name} failed: {str(e)}",
                    agent_id=getattr(worker, 'name', None),
                    role="Worker",
                    task=task
                )
        else:
            work_result = {}
        
        # Next, let the Supervisor review and provide guidance
        supervisor = self.team.get_supervisor()
        if supervisor:
            try:
                supervision_result = supervisor.process({
                    **task,
                    "role": "Supervisor",
                    "action": "review",
                    "work": work_result
                })
                logger.info(f"Supervisor {supervisor.name} provided guidance")
            except Exception as e:
                logger.error(f"Supervisor {supervisor.name} failed: {str(e)}")
                raise AgentExecutionError(
                    f"Supervisor {supervisor.name} failed: {str(e)}",
                    agent_id=getattr(supervisor, 'name', None),
                    role="Supervisor",
                    task=task
                )
        else:
            supervision_result = {}
        
        # Then, let the Evaluator assess the results
        evaluator = self.team.get_evaluator()
        if evaluator:
            try:
                evaluation_result = evaluator.process({
                    **task,
                    "role": "Evaluator",
                    "action": "evaluate",
                    "work": work_result,
                    "supervision": supervision_result
                })
                logger.info(f"Evaluator {evaluator.name} completed evaluation")
            except Exception as e:
                logger.error(f"Evaluator {evaluator.name} failed: {str(e)}")
                raise AgentExecutionError(
                    f"Evaluator {evaluator.name} failed: {str(e)}",
                    agent_id=getattr(evaluator, 'name', None),
                    role="Evaluator",
                    task=task
                )
        else:
            evaluation_result = {}
        
        # Finally, let the Primus make the final decision
        try:
            primus_result = primus.process({
                **task,
                "role": "Primus",
                "action": "decide",
                "design": design_result,
                "work": work_result,
                "supervision": supervision_result,
                "evaluation": evaluation_result
            })
            logger.info(f"Primus {primus.name} made final decision")
        except Exception as e:
            logger.error(f"Primus {primus.name} failed: {str(e)}")
            raise AgentExecutionError(
                f"Primus {primus.name} failed: {str(e)}",
                agent_id=getattr(primus, 'name', None),
                role="Primus",
                task=task
            )
        
        # Check if consensus is required
        if task.get("requires_consensus", False):
            consensus_result = self._resolve_conflicts(
                design_result, 
                work_result, 
                supervision_result, 
                evaluation_result, 
                primus_result
            )
            
            # Return the combined results with consensus
            return {
                "team_result": {
                    "design": design_result,
                    "work": work_result,
                    "supervision": supervision_result,
                    "evaluation": evaluation_result,
                    "primus": primus_result
                },
                "consensus": consensus_result,
                **primus_result  # Include Primus's decision directly in the result
            }
        
        # Return the combined results
        return {
            "team_result": {
                "design": design_result,
                "work": work_result,
                "supervision": supervision_result,
                "evaluation": evaluation_result,
                "primus": primus_result
            },
            **primus_result  # Include Primus's decision directly in the result
        }
    
    def _resolve_conflicts(self, *agent_results) -> Dict[str, Any]:
        """
        Resolve conflicts between agent results.
        
        In case of conflicts, the Primus's decision takes precedence.
        """
        # For now, we'll use a simple approach where the Primus's decision is final
        # This can be extended with more sophisticated conflict resolution strategies
        
        # The last result is from the Primus
        primus_result = agent_results[-1]
        
        # Check if there's a "final_decision" key in the Primus result
        if "final_decision" in primus_result:
            return {"final_decision": primus_result["final_decision"]}
        
        # Otherwise, return a generic consensus result
        return {"consensus": "Reached based on Primus decision"}
