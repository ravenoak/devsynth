"""
Unit tests for the exceptions module.

This module tests the exception hierarchy and functionality defined in src/devsynth/exceptions.py.
"""

from typing import Any, Dict

import pytest

from devsynth.exceptions import (
    AdapterError,
    AgentError,
    AgentPortError,
    ApplicationError,
    CodeGenerationError,
    CommandError,
    ConfigurationError,
    ContextError,
    DevSynthError,
    DialecticalReasoningError,
    DomainError,
    IngestionError,
    InternalError,
    ManifestError,
    MemoryAdapterError,
    MemoryNotFoundError,
    MemoryPortError,
    MemoryStoreError,
    PortError,
    PromiseError,
    PromiseStateError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderPortError,
    ProviderTimeoutError,
    ResourceExhaustedError,
    SystemError,
    TestGenerationException,
    UserInputError,
    ValidationError,
    WorkflowError,
)


class TestDevSynthError:
    """Tests for the base DevSynthError class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_init_with_message_only_succeeds(self):
        """Test initialization with only a message.

        ReqID: N/A"""
        error = DevSynthError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.details == {}
        assert str(error) == "Test error message"

    @pytest.mark.fast
    def test_init_with_error_code_raises_error(self):
        """Test initialization with a message and error code.

        ReqID: N/A"""
        error = DevSynthError("Test error message", error_code="TEST_ERROR")
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {}

    @pytest.mark.fast
    def test_init_with_details_raises_error(self):
        """Test initialization with a message, error code, and details.

        ReqID: N/A"""
        details = {"key": "value", "number": 42}
        error = DevSynthError(
            "Test error message", error_code="TEST_ERROR", details=details
        )
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.details == details

    @pytest.mark.fast
    def test_to_dict_succeeds(self):
        """Test the to_dict method.

        ReqID: N/A"""
        details = {"key": "value", "number": 42}
        error = DevSynthError(
            "Test error message", error_code="TEST_ERROR", details=details
        )
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "DevSynthError"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error message"
        assert error_dict["details"] == details


class TestUserInputErrors:
    """Tests for user input error classes.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_validation_error_raises_error(self):
        """Test ValidationError initialization and properties.

        ReqID: N/A"""
        error = ValidationError(
            message="Invalid input",
            field="username",
            value="",
            constraints={"min_length": 3},
        )
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "username"
        assert error.details["value"] == ""
        assert error.details["constraints"] == {"min_length": 3}
        assert isinstance(error, UserInputError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_configuration_error_raises_error(self):
        """Test ConfigurationError initialization and properties.

        ReqID: N/A"""
        error = ConfigurationError(
            message="Invalid configuration", config_key="api_key", config_value=None
        )
        assert error.message == "Invalid configuration"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details["config_key"] == "api_key"
        assert error.details["config_value"] is None
        assert isinstance(error, UserInputError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_command_error_raises_error(self):
        """Test CommandError initialization and properties.

        ReqID: N/A"""
        error = CommandError(
            message="Command failed", command="generate", args={"model": "gpt-4"}
        )
        assert error.message == "Command failed"
        assert error.error_code == "COMMAND_ERROR"
        assert error.details["command"] == "generate"
        assert error.details["args"] == {"model": "gpt-4"}
        assert isinstance(error, UserInputError)
        assert isinstance(error, DevSynthError)


class TestSystemErrors:
    """Tests for system error classes.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_internal_error_raises_error(self):
        """Test InternalError initialization and properties.

        ReqID: N/A"""
        cause = ValueError("Original error")
        error = InternalError(
            message="Internal system error", component="memory_manager", cause=cause
        )
        assert error.message == "Internal system error"
        assert error.error_code == "INTERNAL_ERROR"
        assert error.details["component"] == "memory_manager"
        assert error.details["original_error"] == "Original error"
        assert error.__cause__ == cause
        assert isinstance(error, SystemError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_resource_exhausted_error_raises_error(self):
        """Test ResourceExhaustedError initialization and properties.

        ReqID: N/A"""
        error = ResourceExhaustedError(
            message="Resource limit reached", resource_type="memory", limit="1GB"
        )
        assert error.message == "Resource limit reached"
        assert error.error_code == "RESOURCE_EXHAUSTED"
        assert error.details["resource_type"] == "memory"
        assert error.details["limit"] == "1GB"
        assert isinstance(error, SystemError)
        assert isinstance(error, DevSynthError)


class TestAdapterErrors:
    """Tests for adapter error classes.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_provider_error_raises_error(self):
        """Test ProviderError initialization and properties.

        ReqID: N/A"""
        provider_error = {"code": 429, "message": "Rate limit exceeded"}
        error = ProviderError(
            message="Provider operation failed",
            provider="openai",
            operation="completion",
            provider_error=provider_error,
        )
        assert error.message == "Provider operation failed"
        assert error.error_code == "PROVIDER_ERROR"
        assert error.details["provider"] == "openai"
        assert error.details["operation"] == "completion"
        assert error.details["provider_error"] == provider_error
        assert isinstance(error, AdapterError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_provider_timeout_error_raises_error(self):
        """Test ProviderTimeoutError initialization and properties.

        ReqID: N/A"""
        error = ProviderTimeoutError(
            message="Provider operation timed out",
            provider="openai",
            operation="completion",
            timeout_seconds=30.0,
        )
        assert error.message == "Provider operation timed out"
        assert error.error_code == "PROVIDER_TIMEOUT"
        assert error.details["provider"] == "openai"
        assert error.details["operation"] == "completion"
        assert error.details["timeout_seconds"] == 30.0
        assert isinstance(error, ProviderError)
        assert isinstance(error, AdapterError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_memory_adapter_error_raises_error(self):
        """Test MemoryAdapterError initialization and properties.

        ReqID: N/A"""
        error = MemoryAdapterError(
            message="Memory operation failed", store_type="vector", operation="search"
        )
        assert error.message == "Memory operation failed"
        assert error.error_code == "MEMORY_ERROR"
        assert error.details["store_type"] == "vector"
        assert error.details["operation"] == "search"
        assert isinstance(error, AdapterError)
        assert isinstance(error, DevSynthError)


class TestDomainErrors:
    """Tests for domain error classes.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_agent_error_raises_error(self):
        """Test AgentError initialization and properties.

        ReqID: N/A"""
        error = AgentError(
            message="Agent operation failed",
            agent_id="planner_agent",
            operation="generate_plan",
        )
        assert error.message == "Agent operation failed"
        assert error.error_code == "AGENT_ERROR"
        assert error.details["agent_id"] == "planner_agent"
        assert error.details["operation"] == "generate_plan"
        assert isinstance(error, DomainError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_workflow_error_succeeds(self):
        """Test WorkflowError initialization and properties.

        ReqID: N/A"""
        error = WorkflowError(
            message="Workflow execution failed",
            workflow_id="code_generation",
            step="generate_tests",
        )
        assert error.message == "Workflow execution failed"
        assert error.error_code == "WORKFLOW_ERROR"
        assert error.details["workflow_id"] == "code_generation"
        assert error.details["step"] == "generate_tests"
        assert isinstance(error, DomainError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_dialectical_reasoning_error_raises_error(self):
        """Test DialecticalReasoningError initialization and properties.

        ReqID: N/A"""
        arguments = ["thesis", "antithesis"]
        error = DialecticalReasoningError(
            message="Reasoning process failed", phase="synthesis", arguments=arguments
        )
        assert error.message == "Reasoning process failed"
        assert error.error_code == "REASONING_ERROR"
        assert error.details["phase"] == "synthesis"
        assert error.details["arguments"] == arguments
        assert isinstance(error, DomainError)
        assert isinstance(error, DevSynthError)


class TestApplicationErrors:
    """Tests for application error classes.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_promise_error_raises_error(self):
        """Test PromiseError initialization and properties.

        ReqID: N/A"""
        error = PromiseError(
            message="Promise operation failed",
            promise_id="promise-123",
            operation="resolve",
        )
        assert error.message == "Promise operation failed"
        assert error.error_code == "PROMISE_ERROR"
        assert error.details["promise_id"] == "promise-123"
        assert error.details["operation"] == "resolve"
        assert isinstance(error, ApplicationError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_promise_state_error_raises_error(self):
        """Test PromiseStateError initialization and properties.

        ReqID: N/A"""
        error = PromiseStateError(
            message="Invalid promise state transition",
            promise_id="promise-123",
            from_state="pending",
            to_state="rejected",
        )
        assert error.message == "Invalid promise state transition"
        assert error.error_code == "PROMISE_STATE_ERROR"
        assert error.details["promise_id"] == "promise-123"
        assert error.details["from_state"] == "pending"
        assert error.details["to_state"] == "rejected"
        assert isinstance(error, PromiseError)
        assert isinstance(error, ApplicationError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_ingestion_error_raises_error(self):
        """Test IngestionError initialization and properties.

        ReqID: N/A"""
        error = IngestionError(
            message="Project ingestion failed",
            phase="expand",
            artifact_path="src/main.py",
        )
        assert error.message == "Project ingestion failed"
        assert error.error_code == "INGESTION_ERROR"
        assert error.details["phase"] == "expand"
        assert error.details["artifact_path"] == "src/main.py"
        assert isinstance(error, ApplicationError)
        assert isinstance(error, DevSynthError)


class TestPortErrors:
    """Tests for port error classes.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_memory_port_error_raises_error(self):
        """Test MemoryPortError initialization and properties.

        ReqID: N/A"""
        error = MemoryPortError(
            message="Memory port operation failed", operation="retrieve"
        )
        assert error.message == "Memory port operation failed"
        assert error.error_code == "MEMORY_PORT_ERROR"
        assert error.details["operation"] == "retrieve"
        assert isinstance(error, PortError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_provider_port_error_raises_error(self):
        """Test ProviderPortError initialization and properties.

        ReqID: N/A"""
        error = ProviderPortError(
            message="Provider port operation failed", operation="generate"
        )
        assert error.message == "Provider port operation failed"
        assert error.error_code == "PROVIDER_PORT_ERROR"
        assert error.details["operation"] == "generate"
        assert isinstance(error, PortError)
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_agent_port_error_raises_error(self):
        """Test AgentPortError initialization and properties.

        ReqID: N/A"""
        error = AgentPortError(
            message="Agent port operation failed", operation="execute"
        )
        assert error.message == "Agent port operation failed"
        assert error.error_code == "AGENT_PORT_ERROR"
        assert error.details["operation"] == "execute"
        assert isinstance(error, PortError)
        assert isinstance(error, DevSynthError)
