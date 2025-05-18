"""
Exceptions for the collaboration module.
"""

from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import (
    DevSynthError,
    CollaborationError as BaseCollaborationError,
    AgentExecutionError as BaseAgentExecutionError,
    ConsensusError as BaseConsensusError,
    RoleAssignmentError as BaseRoleAssignmentError,
    TeamConfigurationError as BaseTeamConfigurationError
)

# Create a logger for this module
logger = DevSynthLogger(__name__)

# For backward compatibility, redefine the exceptions with the same interface
class CollaborationError(BaseCollaborationError):
    """Base exception for collaboration errors."""
    def __init__(self, message, agent_id=None, role=None, task=None, error_code=None):
        super().__init__(message, agent_id=agent_id, role=role, task=task, error_code=error_code)


class AgentExecutionError(BaseAgentExecutionError):
    """Exception raised when an agent fails to execute a task."""
    def __init__(self, message, agent_id=None, role=None, task=None, error_code=None):
        super().__init__(message, agent_id=agent_id, task=task, error_code=error_code)


class ConsensusError(BaseConsensusError):
    """Exception raised when agents cannot reach consensus."""
    def __init__(self, message, agent_id=None, role=None, task=None, agent_ids=None, topic=None, error_code=None):
        super().__init__(
            message, 
            agent_ids=agent_ids or ([agent_id] if agent_id else None), 
            topic=topic, 
            error_code=error_code
        )


class RoleAssignmentError(BaseRoleAssignmentError):
    """Exception raised when there's an issue with role assignment."""
    def __init__(self, message, agent_id=None, role=None, task=None, error_code=None):
        super().__init__(message, agent_id=agent_id, role=role, error_code=error_code)


class TeamConfigurationError(BaseTeamConfigurationError):
    """Exception raised when there's an issue with team configuration."""
    def __init__(self, message, agent_id=None, role=None, task=None, team_id=None, error_code=None):
        super().__init__(message, team_id=team_id, error_code=error_code)
