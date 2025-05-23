"""
Unit tests for the exceptions module.

This module tests the exception hierarchy and functionality defined in src/devsynth/exceptions.py.
"""

import pytest
from typing import Dict, Any

from devsynth.exceptions import (
    DevSynthError,
    UserInputError, ValidationError, ConfigurationError, CommandError,
    SystemError, InternalError, ResourceExhaustedError,
    AdapterError, ProviderError, ProviderTimeoutError, ProviderAuthenticationError,
    MemoryAdapterError, MemoryNotFoundError, MemoryStoreError,
    DomainError, AgentError, WorkflowError, ContextError, DialecticalReasoningError,
    ApplicationError, PromiseError, PromiseStateError, IngestionError, ManifestError,
    CodeGenerationError, TestGenerationError,
    PortError, MemoryPortError, ProviderPortError, AgentPortError
)


class TestDevSynthError:
    """Tests for the base DevSynthError class."""

    def test_init_with_message_only(self):
        """Test initialization with only a message."""
        error = DevSynthError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.details == {}
        assert str(error) == "Test error message"

    def test_init_with_error_code(self):
        """Test initialization with a message and error code."""
        error = DevSynthError("Test error message", error_code="TEST_ERROR")
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {}

    def test_init_with_details(self):
        """Test initialization with a message, error code, and details."""
        details = {"key": "value", "number": 42}
        error = DevSynthError("Test error message", error_code="TEST_ERROR", details=details)
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.details == details

    def test_to_dict(self):
        """Test the to_dict method."""
        details = {"key": "value", "number": 42}
        error = DevSynthError("Test error message", error_code="TEST_ERROR", details=details)
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "DevSynthError"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error message"
        assert error_dict["details"] == details


class TestUserInputErrors:
    """Tests for user input error classes."""

    def test_validation_error(self):
        """Test ValidationError initialization and properties."""
        error = ValidationError(
            message="Invalid input",
            field="username",
            value="",
            constraints={"min_length": 3}
        )
        
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "username"
        assert error.details["value"] == ""
        assert error.details["constraints"] == {"min_length": 3}
        assert isinstance(error, UserInputError)
        assert isinstance(error, DevSynthError)

    def test_configuration_error(self):
        """Test ConfigurationError initialization and properties."""
        error = ConfigurationError(
            message="Invalid configuration",
            config_key="api_key",
            config_value=None
        )
        
        assert error.message == "Invalid configuration"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details["config_key"] == "api_key"
        assert error.details["config_value"] is None
        assert isinstance(error, UserInputError)
        assert isinstance(error, DevSynthError)

    def test_command_error(self):
        """Test CommandError initialization and properties."""
        error = CommandError(
            message="Command failed",
            command="generate",
            args={"model": "gpt-4"}
        )
        
        assert error.message == "Command failed"
        assert error.error_code == "COMMAND_ERROR"
        assert error.details["command"] == "generate"
        assert error.details["args"] == {"model": "gpt-4"}
        assert isinstance(error, UserInputError)
        assert isinstance(error, DevSynthError)


class TestSystemErrors:
    """Tests for system error classes."""

    def test_internal_error(self):
        """Test InternalError initialization and properties."""
        cause = ValueError("Original error")
        error = InternalError(
            message="Internal system error",
            component="memory_manager",
            cause=cause
        )
        
        assert error.message == "Internal system error"
        assert error.error_code == "INTERNAL_ERROR"
        assert error.details["component"] == "memory_manager"
        assert error.details["original_error"] == "Original error"
        assert error.__cause__ == cause
        assert isinstance(error, SystemError)
        assert isinstance(error, DevSynthError)

    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError initialization and properties."""
        error = ResourceExhaustedError(
            message="Resource limit reached",
            resource_type="memory",
            limit="1GB"
        )
        
        assert error.message == "Resource limit reached"
        assert error.error_code == "RESOURCE_EXHAUSTED"
        assert error.details["resource_type"] == "memory"
        assert error.details["limit"] == "1GB"
        assert isinstance(error, SystemError)
        assert isinstance(error, DevSynthError)


class TestAdapterErrors:
    """Tests for adapter error classes."""

    def test_provider_error(self):
        """Test ProviderError initialization and properties."""
        provider_error = {"code": 429, "message": "Rate limit exceeded"}
        error = ProviderError(
            message="Provider operation failed",
            provider="openai",
            operation="completion",
            provider_error=provider_error
        )
        
        assert error.message == "Provider operation failed"
        assert error.error_code == "PROVIDER_ERROR"
        assert error.details["provider"] == "openai"
        assert error.details["operation"] == "completion"
        assert error.details["provider_error"] == provider_error
        assert isinstance(error, AdapterError)
        assert isinstance(error, DevSynthError)

    def test_provider_timeout_error(self):
        """Test ProviderTimeoutError initialization and properties."""
        error = ProviderTimeoutError(
            message="Provider operation timed out",
            provider="openai",
            operation="completion",
            timeout_seconds=30.0
        )
        
        assert error.message == "Provider operation timed out"
        assert error.error_code == "PROVIDER_TIMEOUT"
        assert error.details["provider"] == "openai"
        assert error.details["operation"] == "completion"
        assert error.details["timeout_seconds"] == 30.0
        assert isinstance(error, ProviderError)
        assert isinstance(error, AdapterError)
        assert isinstance(error, DevSynthError)

    def test_memory_adapter_error(self):
        """Test MemoryAdapterError initialization and properties."""
        error = MemoryAdapterError(
            message="Memory operation failed",
            store_type="vector",
            operation="search"
        )
        
        assert error.message == "Memory operation failed"
        assert error.error_code == "MEMORY_ERROR"
        assert error.details["store_type"] == "vector"
        assert error.details["operation"] == "search"
        assert isinstance(error, AdapterError)
        assert isinstance(error, DevSynthError)


class TestDomainErrors:
    """Tests for domain error classes."""

    def test_agent_error(self):
        """Test AgentError initialization and properties."""
        error = AgentError(
            message="Agent operation failed",
            agent_id="planner_agent",
            operation="generate_plan"
        )
        
        assert error.message == "Agent operation failed"
        assert error.error_code == "AGENT_ERROR"
        assert error.details["agent_id"] == "planner_agent"
        assert error.details["operation"] == "generate_plan"
        assert isinstance(error, DomainError)
        assert isinstance(error, DevSynthError)

    def test_workflow_error(self):
        """Test WorkflowError initialization and properties."""
        error = WorkflowError(
            message="Workflow execution failed",
            workflow_id="code_generation",
            step="generate_tests"
        )
        
        assert error.message == "Workflow execution failed"
        assert error.error_code == "WORKFLOW_ERROR"
        assert error.details["workflow_id"] == "code_generation"
        assert error.details["step"] == "generate_tests"
        assert isinstance(error, DomainError)
        assert isinstance(error, DevSynthError)

    def test_dialectical_reasoning_error(self):
        """Test DialecticalReasoningError initialization and properties."""
        arguments = ["thesis", "antithesis"]
        error = DialecticalReasoningError(
            message="Reasoning process failed",
            phase="synthesis",
            arguments=arguments
        )
        
        assert error.message == "Reasoning process failed"
        assert error.error_code == "REASONING_ERROR"
        assert error.details["phase"] == "synthesis"
        assert error.details["arguments"] == arguments
        assert isinstance(error, DomainError)
        assert isinstance(error, DevSynthError)


class TestApplicationErrors:
    """Tests for application error classes."""

    def test_promise_error(self):
        """Test PromiseError initialization and properties."""
        error = PromiseError(
            message="Promise operation failed",
            promise_id="promise-123",
            operation="resolve"
        )
        
        assert error.message == "Promise operation failed"
        assert error.error_code == "PROMISE_ERROR"
        assert error.details["promise_id"] == "promise-123"
        assert error.details["operation"] == "resolve"
        assert isinstance(error, ApplicationError)
        assert isinstance(error, DevSynthError)

    def test_promise_state_error(self):
        """Test PromiseStateError initialization and properties."""
        error = PromiseStateError(
            message="Invalid promise state transition",
            promise_id="promise-123",
            from_state="pending",
            to_state="rejected"
        )
        
        assert error.message == "Invalid promise state transition"
        assert error.error_code == "PROMISE_STATE_ERROR"
        assert error.details["promise_id"] == "promise-123"
        assert error.details["from_state"] == "pending"
        assert error.details["to_state"] == "rejected"
        assert isinstance(error, PromiseError)
        assert isinstance(error, ApplicationError)
        assert isinstance(error, DevSynthError)

    def test_ingestion_error(self):
        """Test IngestionError initialization and properties."""
        error = IngestionError(
            message="Project ingestion failed",
            phase="expand",
            artifact_path="src/main.py"
        )
        
        assert error.message == "Project ingestion failed"
        assert error.error_code == "INGESTION_ERROR"
        assert error.details["phase"] == "expand"
        assert error.details["artifact_path"] == "src/main.py"
        assert isinstance(error, ApplicationError)
        assert isinstance(error, DevSynthError)


class TestPortErrors:
    """Tests for port error classes."""

    def test_memory_port_error(self):
        """Test MemoryPortError initialization and properties."""
        error = MemoryPortError(
            message="Memory port operation failed",
            operation="retrieve"
        )
        
        assert error.message == "Memory port operation failed"
        assert error.error_code == "MEMORY_PORT_ERROR"
        assert error.details["operation"] == "retrieve"
        assert isinstance(error, PortError)
        assert isinstance(error, DevSynthError)

    def test_provider_port_error(self):
        """Test ProviderPortError initialization and properties."""
        error = ProviderPortError(
            message="Provider port operation failed",
            operation="generate"
        )
        
        assert error.message == "Provider port operation failed"
        assert error.error_code == "PROVIDER_PORT_ERROR"
        assert error.details["operation"] == "generate"
        assert isinstance(error, PortError)
        assert isinstance(error, DevSynthError)

    def test_agent_port_error(self):
        """Test AgentPortError initialization and properties."""
        error = AgentPortError(
            message="Agent port operation failed",
            operation="execute"
        )
        
        assert error.message == "Agent port operation failed"
        assert error.error_code == "AGENT_PORT_ERROR"
        assert error.details["operation"] == "execute"
        assert isinstance(error, PortError)
        assert isinstance(error, DevSynthError)