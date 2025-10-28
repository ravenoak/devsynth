import os
import shutil
import tempfile
from collections.abc import Generator

import pytest

from devsynth.application.agents.unified_agent import MVP_CAPABILITIES, UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType


class TestUnifiedAgent:
    """Tests for the UnifiedAgent component.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create a temporary directory for test resources.

        This fixture uses a generator pattern to provide teardown functionality.
        """
        # Setup: Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Yield the directory path to the test
        yield temp_dir

        # Teardown: Remove the temporary directory and all its contents
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def agent(self, temp_dir) -> Generator[UnifiedAgent, None, None]:
        """Create a unified agent for testing.

        This fixture uses a generator pattern to provide teardown functionality.
        It also uses the temp_dir fixture to ensure any files created by the agent
        are isolated and cleaned up after the test.
        """
        # Setup: Create and initialize the agent
        agent = UnifiedAgent()
        config = AgentConfig(
            name="TestUnifiedAgent",
            agent_type=AgentType.ORCHESTRATOR,
            description="Test Unified Agent",
            capabilities=MVP_CAPABILITIES,
            # Add workspace directory to isolate any file operations
            workspace_dir=temp_dir,
        )
        agent.initialize(config)

        # Yield the agent to the test
        yield agent

        # Teardown: Clean up any resources created by the agent
        if hasattr(agent, "cleanup") and callable(agent.cleanup):
            agent.cleanup()

        # If the agent doesn't have a cleanup method, we can add specific cleanup steps here
        # For example, closing connections, releasing locks, etc.

    @pytest.mark.medium
    def test_agent_initialization_succeeds(self, agent):
        """Test that the agent initializes correctly.

        ReqID: N/A"""
        assert agent.name == "TestUnifiedAgent"
        assert agent.agent_type == AgentType.ORCHESTRATOR.value
        assert agent.description == "Test Unified Agent"
        assert agent.get_capabilities() == MVP_CAPABILITIES

    @pytest.mark.medium
    def test_process_specification_task_succeeds(self, agent):
        """Test processing a specification task.

        ReqID: N/A"""
        inputs = {
            "task_type": "specification",
            "requirements": "Build a calculator app",
            "context": "Simple calculator with basic operations",
        }
        result = agent.process(inputs)
        assert "specification" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "specification"

    @pytest.mark.medium
    def test_process_test_task_succeeds(self, agent):
        """Test processing a test task.

        ReqID: N/A"""
        inputs = {
            "task_type": "test",
            "specification": "Calculator app specification",
            "context": "Simple calculator with basic operations",
        }
        result = agent.process(inputs)
        assert "tests" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "code"
        assert result["wsde"].metadata["type"] == "tests"

    @pytest.mark.medium
    def test_process_code_task_succeeds(self, agent):
        """Test processing a code task.

        ReqID: N/A"""
        inputs = {
            "task_type": "code",
            "specification": "Calculator app specification",
            "tests": "Calculator app tests",
            "context": "Simple calculator with basic operations",
        }
        result = agent.process(inputs)
        assert "code" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "code"
        assert result["wsde"].metadata["type"] == "code"

    @pytest.mark.medium
    def test_process_validation_task_is_valid(self, agent):
        """Test processing a validation task.

        ReqID: N/A"""
        inputs = {
            "task_type": "validation",
            "requirements": "Build a calculator app",
            "specification": "Calculator app specification",
            "implementation": "Calculator app implementation",
            "tests": "Calculator app tests",
        }
        result = agent.process(inputs)
        assert "validation" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "validation"

    @pytest.mark.medium
    def test_process_documentation_task_succeeds(self, agent):
        """Test processing a documentation task.

        ReqID: N/A"""
        inputs = {
            "task_type": "documentation",
            "specification": "Calculator app specification",
            "code": "Calculator app implementation",
            "context": "Simple calculator with basic operations",
        }
        result = agent.process(inputs)
        assert "documentation" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "documentation"

    @pytest.mark.medium
    def test_process_project_initialization_task_succeeds(self, agent):
        """Test processing a project initialization task.

        ReqID: N/A"""
        inputs = {
            "task_type": "project_initialization",
            "project_name": "calculator",
            "project_type": "python",
            "context": "Simple calculator with basic operations",
        }
        result = agent.process(inputs)
        assert "project_structure" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "project_structure"

    @pytest.mark.medium
    def test_process_generic_task_succeeds(self, agent):
        """Test processing a generic task without a specific type.

        ReqID: N/A"""
        inputs = {"input": "Process this generic input"}
        result = agent.process(inputs)
        assert "result" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "generic"
