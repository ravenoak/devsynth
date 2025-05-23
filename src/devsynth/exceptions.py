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
    """Exception raised when there's an error in the configuration."""

    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_value: Any = None, error_code: Optional[str] = None):
        details = {
            "config_key": config_key,
            "config_value": config_value
        }
        super().__init__(message, error_code=error_code or "CONFIGURATION_ERROR", details=details)


class CommandError(UserInputError):
    """Exception raised when a command cannot be executed due to user input."""

    def __init__(self, message: str, command: Optional[str] = None,
                 args: Optional[Dict[str, Any]] = None, error_code: Optional[str] = None):
        details = {
            "command": command,
            "args": args or {}
        }
        super().__init__(message, error_code=error_code or "COMMAND_ERROR", details=details)


# System Errors

class SystemError(DevSynthError):
    """Base exception for internal system errors."""
    pass


class InternalError(SystemError):
    """Exception raised for unexpected internal errors."""

    def __init__(self, message: str, component: Optional[str] = None,
                 error_code: Optional[str] = None, cause: Optional[Exception] = None):
        details = {
            "component": component,
            "original_error": str(cause) if cause else None
        }
        super().__init__(message, error_code=error_code or "INTERNAL_ERROR", details=details)
        self.__cause__ = cause


class ResourceExhaustedError(SystemError):
    """Exception raised when a system resource is exhausted."""

    def __init__(self, message: str, resource_type: Optional[str] = None,
                 limit: Any = None, error_code: Optional[str] = None):
        details = {
            "resource_type": resource_type,
            "limit": limit
        }
        super().__init__(message, error_code=error_code or "RESOURCE_EXHAUSTED", details=details)


# Adapter Errors

class AdapterError(DevSynthError):
    """Base exception for errors in adapter components."""
    pass


class ProviderError(AdapterError):
    """Exception raised for errors related to external providers."""

    def __init__(self, message: str, provider: Optional[str] = None,
                 operation: Optional[str] = None, error_code: Optional[str] = None,
                 provider_error: Optional[Dict[str, Any]] = None):
        details = {
            "provider": provider,
            "operation": operation,
            "provider_error": provider_error or {}
        }
        super().__init__(message, error_code=error_code or "PROVIDER_ERROR", details=details)


class ProviderTimeoutError(ProviderError):
    """Exception raised when a provider operation times out."""

    def __init__(self, message: str, provider: Optional[str] = None,
                 operation: Optional[str] = None, timeout_seconds: Optional[float] = None):
        details = {
            "provider": provider,
            "operation": operation,
            "timeout_seconds": timeout_seconds
        }
        super().__init__(message, error_code="PROVIDER_TIMEOUT", details=details)


class ProviderAuthenticationError(ProviderError):
    """Exception raised when authentication with a provider fails."""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message, provider=provider, error_code="PROVIDER_AUTHENTICATION_ERROR")


class MemoryAdapterError(AdapterError):
    """Exception raised for errors related to the memory system."""

    def __init__(self, message: str, store_type: Optional[str] = None,
                 operation: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "store_type": store_type,
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "MEMORY_ERROR", details=details)


class MemoryNotFoundError(MemoryAdapterError):
    """Exception raised when an item is not found in memory."""

    def __init__(self, message: str, item_id: Optional[str] = None,
                 store_type: Optional[str] = None):
        details = {
            "item_id": item_id,
            "store_type": store_type
        }
        super().__init__(message, error_code="MEMORY_NOT_FOUND", details=details)


class MemoryStoreError(MemoryAdapterError):
    """Exception raised when there's an error with a memory store operation."""

    def __init__(self, message: str, store_type: Optional[str] = None,
                 operation: Optional[str] = None, original_error: Optional[Exception] = None):
        details = {
            "store_type": store_type,
            "operation": operation,
            "original_error": str(original_error) if original_error else None
        }
        super().__init__(message, error_code="MEMORY_STORE_ERROR", details=details)
        self.__cause__ = original_error


# Domain Errors

class DomainError(DevSynthError):
    """Base exception for errors in domain logic."""
    pass


class AgentError(DomainError):
    """Exception raised for errors related to agents."""

    def __init__(self, message: str, agent_id: Optional[str] = None,
                 operation: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "agent_id": agent_id,
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "AGENT_ERROR", details=details)


class WorkflowError(DomainError):
    """Exception raised for errors in workflow execution."""

    def __init__(self, message: str, workflow_id: Optional[str] = None,
                 step: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "workflow_id": workflow_id,
            "step": step
        }
        super().__init__(message, error_code=error_code or "WORKFLOW_ERROR", details=details)


class ContextError(DomainError):
    """Exception raised for errors related to context management."""

    def __init__(self, message: str, context_id: Optional[str] = None,
                 operation: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "context_id": context_id,
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "CONTEXT_ERROR", details=details)


class DialecticalReasoningError(DomainError):
    """Exception raised for errors in dialectical reasoning processes."""

    def __init__(self, message: str, phase: Optional[str] = None,
                 arguments: Optional[List[str]] = None, error_code: Optional[str] = None):
        details = {
            "phase": phase,
            "arguments": arguments
        }
        super().__init__(message, error_code=error_code or "REASONING_ERROR", details=details)


# Application Errors

class ApplicationError(DevSynthError):
    """Base exception for errors in application logic."""
    pass


class PromiseError(ApplicationError):
    """Exception raised for errors related to the Promise system."""

    def __init__(self, message: str, promise_id: Optional[str] = None,
                 operation: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "promise_id": promise_id,
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "PROMISE_ERROR", details=details)


class PromiseStateError(PromiseError):
    """Exception raised when an invalid promise state transition is attempted."""

    def __init__(self, message: str, promise_id: Optional[str] = None,
                 from_state: Optional[str] = None, to_state: Optional[str] = None):
        details = {
            "promise_id": promise_id,
            "from_state": from_state,
            "to_state": to_state
        }
        super().__init__(message, error_code="PROMISE_STATE_ERROR", details=details)


class IngestionError(ApplicationError):
    """Exception raised for errors during project ingestion."""

    def __init__(self, message: str, phase: Optional[str] = None,
                 artifact_path: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "phase": phase,
            "artifact_path": artifact_path
        }
        super().__init__(message, error_code=error_code or "INGESTION_ERROR", details=details)


class ManifestError(ApplicationError):
    """Exception raised for errors related to the project manifest."""

    def __init__(self, message: str, field: Optional[str] = None,
                 manifest_path: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "field": field,
            "manifest_path": manifest_path
        }
        super().__init__(message, error_code=error_code or "MANIFEST_ERROR", details=details)


class CodeGenerationError(ApplicationError):
    """Exception raised for errors during code generation."""

    def __init__(self, message: str, language: Optional[str] = None,
                 component: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "language": language,
            "component": component
        }
        super().__init__(message, error_code=error_code or "CODE_GENERATION_ERROR", details=details)


class TestGenerationError(ApplicationError):
    """Exception raised for errors during test generation."""

    def __init__(self, message: str, test_type: Optional[str] = None,
                 target: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "test_type": test_type,
            "target": target
        }
        super().__init__(message, error_code=error_code or "TEST_GENERATION_ERROR", details=details)


# Ports Errors

class PortError(DevSynthError):
    """Base exception for errors in port interfaces."""
    pass


class MemoryPortError(PortError):
    """Exception raised for errors in memory port operations."""

    def __init__(self, message: str, operation: Optional[str] = None,
                 error_code: Optional[str] = None):
        details = {
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "MEMORY_PORT_ERROR", details=details)


class ProviderPortError(PortError):
    """Exception raised for errors in provider port operations."""

    def __init__(self, message: str, operation: Optional[str] = None,
                 error_code: Optional[str] = None):
        details = {
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "PROVIDER_PORT_ERROR", details=details)


class AgentPortError(PortError):
    """Exception raised for errors in agent port operations."""

    def __init__(self, message: str, operation: Optional[str] = None,
                 error_code: Optional[str] = None):
        details = {
            "operation": operation
        }
        super().__init__(message, error_code=error_code or "AGENT_PORT_ERROR", details=details)


# Initialize logger at the end to avoid circular imports
try:
    from devsynth.logging_setup import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
