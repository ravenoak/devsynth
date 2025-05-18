
"""
Hierarchical exception structure for the DevSynth system.

This module defines a comprehensive exception hierarchy for the DevSynth system,
providing specific exception types for different categories of errors.
"""

from typing import Optional, Dict, Any, List

# Import will be done after DevSynthLogger is defined to avoid circular imports
# Logger will be initialized at the end of the file


class DevSynthError(Exception):
    """Base exception class for all DevSynth errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# User Input Errors

class UserInputError(DevSynthError):
    """Base exception for errors related to user input."""
    pass


class ValidationError(UserInputError):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, 
                 constraints: Optional[Dict[str, Any]] = None, error_code: Optional[str] = None):
        details = {
            "field": field,
            "value": value,
            "constraints": constraints or {}
        }
        super().__init__(message, error_code=error_code or "VALIDATION_ERROR", details=details)


class ConfigurationError(UserInputError):
    """Exception raised when there's an issue with configuration."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, error_code: Optional[str] = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, error_code=error_code or "CONFIG_ERROR", details=details)


# LLM API Errors

class LLMError(DevSynthError):
    """Base exception for errors related to LLM API interactions."""
    pass


class LLMAPIError(LLMError):
    """Exception raised when there's an issue with the LLM API."""
    
    def __init__(self, message: str, provider: Optional[str] = None, model: Optional[str] = None, 
                 status_code: Optional[int] = None, error_code: Optional[str] = None):
        details = {
            "provider": provider,
            "model": model,
            "status_code": status_code
        }
        super().__init__(message, error_code=error_code or "LLM_API_ERROR", details=details)


class TokenLimitExceededError(LLMError):
    """Exception raised when the token limit is exceeded."""
    
    def __init__(self, message: str, current_tokens: int, max_tokens: int, error_code: Optional[str] = None):
        details = {
            "current_tokens": current_tokens,
            "max_tokens": max_tokens,
            "excess": current_tokens - max_tokens
        }
        super().__init__(message, error_code=error_code or "TOKEN_LIMIT_EXCEEDED", details=details)


class ModelUnavailableError(LLMError):
    """Exception raised when an LLM model is unavailable."""
    
    def __init__(self, message: str, provider: Optional[str] = None, model: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "provider": provider,
            "model": model
        }
        super().__init__(message, error_code=error_code or "MODEL_UNAVAILABLE", details=details)


# File System Errors

class FileSystemError(DevSynthError):
    """Base exception for file system errors."""
    pass


class FileNotFoundError(FileSystemError):
    """Exception raised when a file is not found."""
    
    def __init__(self, message: str, file_path: str, error_code: Optional[str] = None):
        details = {"file_path": file_path}
        super().__init__(message, error_code=error_code or "FILE_NOT_FOUND", details=details)


class FilePermissionError(FileSystemError):
    """Exception raised when permission is denied for a file operation."""
    
    def __init__(self, message: str, file_path: str, operation: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "file_path": file_path,
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "FILE_PERMISSION_DENIED", details=details)


class FileOperationError(FileSystemError):
    """Exception raised when a file operation fails."""
    
    def __init__(self, message: str, file_path: str, operation: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "file_path": file_path,
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "FILE_OPERATION_FAILED", details=details)


# Memory System Errors

class MemoryError(DevSynthError):
    """Base exception for memory system errors."""
    pass


class MemoryStoreError(MemoryError):
    """Exception raised when a memory store operation fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None, item_id: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "operation": operation,
            "item_id": item_id
        }
        super().__init__(message, error_code=error_code or "MEMORY_STORE_ERROR", details=details)


class MemoryItemNotFoundError(MemoryError):
    """Exception raised when a memory item is not found."""
    
    def __init__(self, message: str, item_id: str, error_code: Optional[str] = None):
        details = {"item_id": item_id}
        super().__init__(message, error_code=error_code or "MEMORY_ITEM_NOT_FOUND", details=details)


class MemoryCorruptionError(MemoryError):
    """Exception raised when memory data is corrupted."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, error_code: Optional[str] = None):
        details = {"file_path": file_path} if file_path else {}
        super().__init__(message, error_code=error_code or "MEMORY_CORRUPTION", details=details)


# Agent System Errors

class AgentError(DevSynthError):
    """Base exception for agent system errors."""
    pass


class AgentInitializationError(AgentError):
    """Exception raised when an agent fails to initialize."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, agent_type: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "agent_id": agent_id,
            "agent_type": agent_type
        }
        super().__init__(message, error_code=error_code or "AGENT_INIT_ERROR", details=details)


class AgentExecutionError(AgentError):
    """Exception raised when an agent fails to execute a task."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, task: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "agent_id": agent_id,
            "task": task
        }
        super().__init__(message, error_code=error_code or "AGENT_EXECUTION_ERROR", details=details)


class AgentStateError(AgentError):
    """Exception raised when an agent is in an invalid state for an operation."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, current_state: Optional[str] = None, 
                 expected_state: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "agent_id": agent_id,
            "current_state": current_state,
            "expected_state": expected_state
        }
        super().__init__(message, error_code=error_code or "AGENT_STATE_ERROR", details=details)


# Orchestration Errors

class OrchestrationError(DevSynthError):
    """Base exception for orchestration errors."""
    pass


class WorkflowError(OrchestrationError):
    """Exception raised when there's an issue with a workflow."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, step: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "workflow_id": workflow_id,
            "step": step
        }
        super().__init__(message, error_code=error_code or "WORKFLOW_ERROR", details=details)


class WorkflowStepError(WorkflowError):
    """Exception raised when a workflow step fails."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, step: Optional[str] = None, 
                 step_index: Optional[int] = None, error_code: Optional[str] = None):
        details = {
            "workflow_id": workflow_id,
            "step": step,
            "step_index": step_index
        }
        super().__init__(message, error_code=error_code or "WORKFLOW_STEP_ERROR", details=details)


class NeedsHumanInterventionError(OrchestrationError):
    """Exception raised when human intervention is needed."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, step: Optional[str] = None, 
                 reason: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "workflow_id": workflow_id,
            "step": step,
            "reason": reason
        }
        super().__init__(message, error_code=error_code or "NEEDS_HUMAN_INTERVENTION", details=details)


# Collaboration Errors

class CollaborationError(DevSynthError):
    """Base exception for collaboration errors."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, role: Optional[str] = None, 
                 task: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "agent_id": agent_id,
            "role": role,
            "task": task
        }
        super().__init__(message, error_code=error_code or "COLLABORATION_ERROR", details=details)


class ConsensusError(CollaborationError):
    """Exception raised when agents cannot reach consensus."""
    
    def __init__(self, message: str, agent_ids: Optional[List[str]] = None, topic: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "agent_ids": agent_ids,
            "topic": topic
        }
        super().__init__(message, error_code=error_code or "CONSENSUS_ERROR", details=details)


class RoleAssignmentError(CollaborationError):
    """Exception raised when there's an issue with role assignment."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, role: Optional[str] = None, 
                 error_code: Optional[str] = None):
        details = {
            "agent_id": agent_id,
            "role": role
        }
        super().__init__(message, error_code=error_code or "ROLE_ASSIGNMENT_ERROR", details=details)


class TeamConfigurationError(CollaborationError):
    """Exception raised when there's an issue with team configuration."""
    
    def __init__(self, message: str, team_id: Optional[str] = None, error_code: Optional[str] = None):
        details = {"team_id": team_id} if team_id else {}
        super().__init__(message, error_code=error_code or "TEAM_CONFIG_ERROR", details=details)


# Internal Application Errors

class InternalError(DevSynthError):
    """Base exception for internal application errors."""
    pass


class DependencyError(InternalError):
    """Exception raised when there's an issue with a dependency."""
    
    def __init__(self, message: str, dependency: Optional[str] = None, error_code: Optional[str] = None):
        details = {"dependency": dependency} if dependency else {}
        super().__init__(message, error_code=error_code or "DEPENDENCY_ERROR", details=details)


class ResourceExhaustionError(InternalError):
    """Exception raised when a resource is exhausted."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, limit: Optional[int] = None, 
                 error_code: Optional[str] = None):
        details = {
            "resource_type": resource_type,
            "limit": limit
        }
        super().__init__(message, error_code=error_code or "RESOURCE_EXHAUSTION", details=details)


class UnexpectedStateError(InternalError):
    """Exception raised when the system is in an unexpected state."""
    
    def __init__(self, message: str, component: Optional[str] = None, current_state: Optional[str] = None, 
                 expected_state: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "component": component,
            "current_state": current_state,
            "expected_state": expected_state
        }
        super().__init__(message, error_code=error_code or "UNEXPECTED_STATE", details=details)


# Logger will be initialized later to avoid circular imports
# We'll use a standard Python logger for now
import logging
logger = logging.getLogger(__name__)
