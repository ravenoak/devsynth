import pytest
from devsynth.application.agents.unified_agent import UnifiedAgent, MVP_CAPABILITIES
from devsynth.domain.models.agent import AgentConfig, AgentType

class TestUnifiedAgent:
    @pytest.fixture
    def agent(self):
        """Create a unified agent for testing."""
        agent = UnifiedAgent()
        config = AgentConfig(
            name="TestUnifiedAgent",
            agent_type=AgentType.ORCHESTRATOR,
            description="Test Unified Agent",
            capabilities=MVP_CAPABILITIES
        )
        agent.initialize(config)
        return agent
    
    def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.name == "TestUnifiedAgent"
        assert agent.agent_type == AgentType.ORCHESTRATOR.value
        assert agent.description == "Test Unified Agent"
        assert agent.get_capabilities() == MVP_CAPABILITIES
    
    def test_process_specification_task(self, agent):
        """Test processing a specification task."""
        inputs = {
            "task_type": "specification",
            "requirements": "Build a calculator app",
            "context": "Simple calculator with basic operations"
        }
        
        result = agent.process(inputs)
        
        assert "specification" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "specification"
    
    def test_process_test_task(self, agent):
        """Test processing a test task."""
        inputs = {
            "task_type": "test",
            "specification": "Calculator app specification",
            "context": "Simple calculator with basic operations"
        }
        
        result = agent.process(inputs)
        
        assert "tests" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "code"
        assert result["wsde"].metadata["type"] == "tests"
    
    def test_process_code_task(self, agent):
        """Test processing a code task."""
        inputs = {
            "task_type": "code",
            "specification": "Calculator app specification",
            "tests": "Calculator app tests",
            "context": "Simple calculator with basic operations"
        }
        
        result = agent.process(inputs)
        
        assert "code" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "code"
        assert result["wsde"].metadata["type"] == "code"
    
    def test_process_validation_task(self, agent):
        """Test processing a validation task."""
        inputs = {
            "task_type": "validation",
            "requirements": "Build a calculator app",
            "specification": "Calculator app specification",
            "implementation": "Calculator app implementation",
            "tests": "Calculator app tests"
        }
        
        result = agent.process(inputs)
        
        assert "validation" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "validation"
    
    def test_process_documentation_task(self, agent):
        """Test processing a documentation task."""
        inputs = {
            "task_type": "documentation",
            "specification": "Calculator app specification",
            "code": "Calculator app implementation",
            "context": "Simple calculator with basic operations"
        }
        
        result = agent.process(inputs)
        
        assert "documentation" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "documentation"
    
    def test_process_project_initialization_task(self, agent):
        """Test processing a project initialization task."""
        inputs = {
            "task_type": "project_initialization",
            "project_name": "calculator",
            "project_type": "python",
            "context": "Simple calculator with basic operations"
        }
        
        result = agent.process(inputs)
        
        assert "project_structure" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "project_structure"
    
    def test_process_generic_task(self, agent):
        """Test processing a generic task without a specific type."""
        inputs = {
            "input": "Process this generic input"
        }
        
        result = agent.process(inputs)
        
        assert "result" in result
        assert "wsde" in result
        assert result["agent"] == agent.name
        assert result["wsde"].content_type == "text"
        assert result["wsde"].metadata["type"] == "generic"
