"""
Hierarchical exception structure for the DevSynth system.

This module defines a comprehensive exception hierarchy for the DevSynth system,
providing specific exception types for different categories of errors.
"""

import logging
from typing import Any

# Logger will be initialized at the end of the file


class DevSynthError(Exception):
    """Base exception class for all DevSynth errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message: str = message
        self.error_code: str | None = error_code
        self.details: dict[str, Any] = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert the exception to a dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# User Input Errors


class UserInputError(DevSynthError):
    """Base exception for errors related to user input."""

    pass


class ValidationError(UserInputError):
    """Exception raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        constraints: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"field": field, "value": value, "constraints": constraints or {}}
        super().__init__(
            message, error_code=error_code or "VALIDATION_ERROR", details=details
        )


class ConfigurationError(UserInputError):
    """Exception raised when there's an error in the configuration."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: Any = None,
        error_code: str | None = None,
    ) -> None:
        details = {"config_key": config_key, "config_value": config_value}
        super().__init__(
            message, error_code=error_code or "CONFIGURATION_ERROR", details=details
        )


class CommandError(UserInputError):
    """Exception raised when a command cannot be executed due to user input."""

    def __init__(
        self,
        message: str,
        command: str | None = None,
        args: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"command": command, "args": args or {}}
        super().__init__(
            message, error_code=error_code or "COMMAND_ERROR", details=details
        )


# System Errors


class SystemError(DevSynthError):
    """Base exception for internal system errors."""

    pass


class InternalError(SystemError):
    """Exception raised for unexpected internal errors."""

    def __init__(
        self,
        message: str,
        component: str | None = None,
        error_code: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = {
            "component": component,
            "original_error": str(cause) if cause else None,
        }
        super().__init__(
            message, error_code=error_code or "INTERNAL_ERROR", details=details
        )
        self.__cause__: Exception | None = cause


class ResourceExhaustedError(SystemError):
    """Exception raised when a system resource is exhausted."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        limit: Any = None,
        error_code: str | None = None,
    ) -> None:
        details = {"resource_type": resource_type, "limit": limit}
        super().__init__(
            message, error_code=error_code or "RESOURCE_EXHAUSTED", details=details
        )


# Adapter Errors


class AdapterError(DevSynthError):
    """Base exception for errors in adapter components."""

    pass


class MemoryError(DevSynthError):
    """Base exception for memory system errors."""

    pass


class MemoryCorruptionError(MemoryError):
    """Exception raised when memory data is corrupted."""

    def __init__(
        self,
        message: str,
        store_type: str | None = None,
        item_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"store_type": store_type, "item_id": item_id}
        super().__init__(
            message, error_code=error_code or "MEMORY_CORRUPTION", details=details
        )


class ProviderError(AdapterError):
    """Exception raised for errors related to external providers."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
        provider_error: dict[str, Any] | None = None,
    ) -> None:
        details = {
            "provider": provider,
            "operation": operation,
            "provider_error": provider_error or {},
        }
        super().__init__(
            message, error_code=error_code or "PROVIDER_ERROR", details=details
        )


class LLMError(ProviderError):
    """Exception raised for errors related to LLM operations."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
        provider_error: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            provider=provider,
            operation=operation,
            error_code=error_code or "LLM_ERROR",
            provider_error=provider_error,
        )


class TokenLimitExceededError(LLMError):
    """Exception raised when a text exceeds the token limit."""

    def __init__(
        self,
        message: str,
        current_tokens: int,
        max_tokens: int,
        provider: str | None = None,
        operation: str | None = None,
    ) -> None:
        details = {
            "current_tokens": current_tokens,
            "max_tokens": max_tokens,
            "excess": current_tokens - max_tokens,
        }
        super().__init__(
            message,
            provider=provider,
            operation=operation,
            error_code="TOKEN_LIMIT_EXCEEDED",
            provider_error=details,
        )


class ProviderTimeoutError(ProviderError):
    """Exception raised when a provider operation times out."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        # Call parent constructor
        super().__init__(
            message,
            provider=provider,
            operation=operation,
            error_code="PROVIDER_TIMEOUT",
        )

        # Add timeout_seconds directly to the details dictionary
        self.details["timeout_seconds"] = timeout_seconds


class ProviderAuthenticationError(ProviderError):
    """Exception raised when authentication with a provider fails."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(
            message, provider=provider, error_code="PROVIDER_AUTHENTICATION_ERROR"
        )


class MemoryAdapterError(AdapterError):
    """Exception raised for errors related to the memory system."""

    def __init__(
        self,
        message: str,
        store_type: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"store_type": store_type, "operation": operation}
        super().__init__(
            message, error_code=error_code or "MEMORY_ERROR", details=details
        )


class MemoryNotFoundError(MemoryAdapterError):
    """Exception raised when an item is not found in memory."""

    def __init__(
        self,
        message: str,
        item_id: str | None = None,
        store_type: str | None = None,
    ) -> None:
        super().__init__(
            message,
            store_type=store_type,
            error_code="MEMORY_NOT_FOUND",
        )
        if item_id:
            self.details["item_id"] = item_id


class MemoryItemNotFoundError(MemoryAdapterError):
    """Exception raised when a specific memory item is not found."""

    def __init__(
        self,
        message: str,
        item_id: str | None = None,
        store_type: str | None = None,
    ) -> None:
        super().__init__(
            message,
            store_type=store_type,
            error_code="MEMORY_ITEM_NOT_FOUND",
        )
        if item_id:
            self.details["item_id"] = item_id


class MemoryStoreError(MemoryAdapterError):
    """Exception raised when there's an error with a memory store operation."""

    def __init__(
        self,
        message: str,
        store_type: str | None = None,
        operation: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        # Call parent constructor with the appropriate parameters
        super().__init__(
            message,
            store_type=store_type,
            operation=operation,
            error_code="MEMORY_STORE_ERROR",
        )

        # Add original_error to details dictionary
        if original_error:
            self.details["original_error"] = str(original_error)

        # Set the cause for proper exception chaining
        self.__cause__: Exception | None = original_error


class MemoryTransactionError(MemoryAdapterError):
    """Exception raised when a memory transaction operation fails."""

    def __init__(
        self,
        message: str,
        transaction_id: str | None = None,
        store_type: str | None = None,
        operation: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        # Call parent constructor with the appropriate parameters
        super().__init__(
            message,
            store_type=store_type,
            operation=operation,
            error_code="MEMORY_TRANSACTION_ERROR",
        )

        # Store transaction_id
        self.transaction_id: str | None = transaction_id

        # Add transaction_id and original_error to details dictionary
        if transaction_id:
            self.details["transaction_id"] = transaction_id
        if original_error:
            self.details["original_error"] = str(original_error)

        # Set the cause for proper exception chaining
        self.__cause__: Exception | None = original_error


class CircuitBreakerOpenError(MemoryAdapterError):
    """Exception raised when a circuit breaker is open."""

    def __init__(
        self,
        message: str,
        circuit_name: str | None = None,
        reset_time: float | None = None,
        store_type: str | None = None,
        operation: str | None = None,
    ) -> None:
        # Call parent constructor with the appropriate parameters
        super().__init__(
            message,
            store_type=store_type,
            operation=operation,
            error_code="CIRCUIT_BREAKER_OPEN_ERROR",
        )

        # Store circuit_name and reset_time
        self.circuit_name: str | None = circuit_name
        self.reset_time: float | None = reset_time

        # Add circuit_name and reset_time to details dictionary
        if circuit_name:
            self.details["circuit_name"] = circuit_name
        if reset_time:
            self.details["reset_time"] = reset_time


# Domain Errors


class DomainError(DevSynthError):
    """Base exception for errors in domain logic."""

    pass


class AgentError(DomainError):
    """Exception raised for errors related to agents."""

    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"agent_id": agent_id, "operation": operation}
        super().__init__(
            message, error_code=error_code or "AGENT_ERROR", details=details
        )


class WorkflowError(DomainError):
    """Exception raised for errors in workflow execution."""

    def __init__(
        self,
        message: str,
        workflow_id: str | None = None,
        step: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"workflow_id": workflow_id, "step": step}
        super().__init__(
            message, error_code=error_code or "WORKFLOW_ERROR", details=details
        )


class NeedsHumanInterventionError(WorkflowError):
    """Exception raised when a workflow needs human intervention."""

    def __init__(
        self,
        message: str,
        workflow_id: str | None = None,
        step: str | None = None,
        options: list[str] | None = None,
    ) -> None:
        # Create details dictionary for this class
        self.options: list[str] = options or []

        # Call parent constructor without passing details
        super().__init__(
            message,
            workflow_id=workflow_id,
            step=step,
            error_code="NEEDS_HUMAN_INTERVENTION",
        )


class ContextError(DomainError):
    """Exception raised for errors related to context management."""

    def __init__(
        self,
        message: str,
        context_id: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"context_id": context_id, "operation": operation}
        super().__init__(
            message, error_code=error_code or "CONTEXT_ERROR", details=details
        )


class DialecticalReasoningError(DomainError):
    """Exception raised for errors in dialectical reasoning processes."""

    def __init__(
        self,
        message: str,
        phase: str | None = None,
        arguments: list[str] | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"phase": phase, "arguments": arguments}
        super().__init__(
            message, error_code=error_code or "REASONING_ERROR", details=details
        )


class ProjectModelError(DomainError):
    """Exception raised for errors related to the project model."""

    def __init__(
        self,
        message: str,
        model_id: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"model_id": model_id, "operation": operation}
        super().__init__(
            message, error_code=error_code or "PROJECT_MODEL_ERROR", details=details
        )


# Application Errors


class ApplicationError(DevSynthError):
    """Base exception for errors in application logic."""

    pass


class PromiseError(ApplicationError):
    """Exception raised for errors related to the Promise system."""

    def __init__(
        self,
        message: str,
        promise_id: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"promise_id": promise_id, "operation": operation}
        super().__init__(
            message, error_code=error_code or "PROMISE_ERROR", details=details
        )


class PromiseStateError(PromiseError):
    """Exception raised when an invalid promise state transition is attempted."""

    def __init__(
        self,
        message: str,
        promise_id: str | None = None,
        from_state: str | None = None,
        to_state: str | None = None,
    ) -> None:
        # Call parent constructor with state_transition as the operation
        super().__init__(
            message,
            promise_id=promise_id,
            operation="state_transition",
            error_code="PROMISE_STATE_ERROR",
        )

        # Add from_state and to_state directly to the details dictionary
        self.details["from_state"] = from_state
        self.details["to_state"] = to_state


class IngestionError(ApplicationError):
    """Exception raised for errors during project ingestion."""

    def __init__(
        self,
        message: str,
        phase: str | None = None,
        artifact_path: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"phase": phase, "artifact_path": artifact_path}
        super().__init__(
            message, error_code=error_code or "INGESTION_ERROR", details=details
        )


class DocumentationError(ApplicationError):
    """Exception raised for errors related to documentation processing."""

    def __init__(
        self,
        message: str,
        doc_type: str | None = None,
        doc_path: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"doc_type": doc_type, "doc_path": doc_path}
        super().__init__(
            message, error_code=error_code or "DOCUMENTATION_ERROR", details=details
        )


class ManifestError(ApplicationError):
    """Exception raised for errors related to the project manifest."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        manifest_path: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"field": field, "manifest_path": manifest_path}
        super().__init__(
            message, error_code=error_code or "MANIFEST_ERROR", details=details
        )


class CodeGenerationError(ApplicationError):
    """Exception raised for errors during code generation."""

    def __init__(
        self,
        message: str,
        language: str | None = None,
        component: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"language": language, "component": component}
        super().__init__(
            message, error_code=error_code or "CODE_GENERATION_ERROR", details=details
        )


class TestGenerationException(ApplicationError):
    """Exception raised for errors during test generation."""

    __test__ = False

    def __init__(
        self,
        message: str,
        test_type: str | None = None,
        target: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"test_type": test_type, "target": target}
        super().__init__(
            message, error_code=error_code or "TEST_GENERATION_ERROR", details=details
        )


class EDRRCoordinatorError(ApplicationError):
    """Exception raised for errors in the EDRR coordinator."""

    def __init__(
        self,
        message: str,
        phase: str | None = None,
        component: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"phase": phase, "component": component}
        super().__init__(
            message, error_code=error_code or "EDRR_COORDINATOR_ERROR", details=details
        )


# Collaboration Errors


class CollaborationError(DomainError):
    """Base exception for collaboration errors."""

    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        role: str | None = None,
        task: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"agent_id": agent_id, "role": role, "task": task}
        super().__init__(
            message, error_code=error_code or "COLLABORATION_ERROR", details=details
        )


class AgentExecutionError(CollaborationError):
    """Exception raised when an agent fails to execute a task."""

    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        task: str | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(
            message,
            agent_id=agent_id,
            task=task,
            error_code=error_code or "AGENT_EXECUTION_ERROR",
        )


class ConsensusError(CollaborationError):
    """Exception raised when agents cannot reach consensus."""

    def __init__(
        self,
        message: str,
        agent_ids: list[str] | None = None,
        topic: str | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code or "CONSENSUS_ERROR")
        self.details.update({"agent_ids": agent_ids, "topic": topic})


class RoleAssignmentError(CollaborationError):
    """Exception raised when there's an issue with role assignment."""

    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        role: str | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(
            message,
            agent_id=agent_id,
            role=role,
            error_code=error_code or "ROLE_ASSIGNMENT_ERROR",
        )


class TeamConfigurationError(CollaborationError):
    """Exception raised when there's an issue with team configuration."""

    def __init__(
        self,
        message: str,
        team_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code or "TEAM_CONFIGURATION_ERROR")
        self.details["team_id"] = team_id


# Ports Errors


class PortError(DevSynthError):
    """Base exception for errors in port interfaces."""

    pass


class MemoryPortError(PortError):
    """Exception raised for errors in memory port operations."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"operation": operation}
        super().__init__(
            message, error_code=error_code or "MEMORY_PORT_ERROR", details=details
        )


class ProviderPortError(PortError):
    """Exception raised for errors in provider port operations."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"operation": operation}
        super().__init__(
            message, error_code=error_code or "PROVIDER_PORT_ERROR", details=details
        )


class AgentPortError(PortError):
    """Exception raised for errors in agent port operations."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"operation": operation}
        super().__init__(
            message, error_code=error_code or "AGENT_PORT_ERROR", details=details
        )


# File System Errors


class FileSystemError(DevSynthError):
    """Base exception for file system errors."""

    pass


class FileNotFoundError(FileSystemError):
    """Exception raised when a file is not found."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"file_path": file_path}
        super().__init__(
            message, error_code=error_code or "FILE_NOT_FOUND", details=details
        )


class FilePermissionError(FileSystemError):
    """Exception raised when there's a permission error with a file."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {"file_path": file_path, "operation": operation}
        super().__init__(
            message, error_code=error_code or "FILE_PERMISSION_ERROR", details=details
        )


class FileOperationError(FileSystemError):
    """Exception raised when a file operation fails."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        original_error: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        details = {
            "file_path": file_path,
            "operation": operation,
            "original_error": str(original_error) if original_error else None,
        }
        super().__init__(
            message, error_code=error_code or "FILE_OPERATION_ERROR", details=details
        )
        self.__cause__: Exception | None = original_error


# Security Errors


class SecurityError(ApplicationError):
    """Base exception for security-related errors."""

    pass


class AuthenticationError(SecurityError):
    """Exception raised when authentication fails."""


class AuthorizationError(SecurityError):
    """Exception raised when a user lacks required permissions."""


class InputSanitizationError(SecurityError):
    """Exception raised when unsafe input is detected."""


# Initialize logger at the end to avoid circular imports
logger = logging.getLogger(__name__)


def log_exception(exc: DevSynthError, *, level: int = logging.ERROR) -> None:
    """Log a :class:`DevSynthError` with structured details."""

    log_fn = getattr(logger, "log", None)
    if callable(log_fn):
        log_fn(level, exc.message, extra={"error": exc.to_dict()})
    else:  # Fallback for DevSynthLogger without ``log`` method
        logger.error(exc.message, extra={"error": exc.to_dict()})
