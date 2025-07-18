import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.agents.multi_language_code import MultiLanguageCodeAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestMultiLanguageCodeAgent:
    @pytest.fixture
    def mock_llm_port(self):
        mock = MagicMock(spec=LLMPort)
        mock.generate.return_value = 'generated code'
        mock.generate_with_context.return_value = 'generated code with context'
        return mock

    @pytest.fixture
    def agent(self, mock_llm_port):
        agent = MultiLanguageCodeAgent()
        config = AgentConfig(
            name='MultiLangAgent',
            agent_type=AgentType.CODE,
            description='Test multi language agent',
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization_succeeds(self, agent):
        assert agent.name == 'MultiLangAgent'
        assert agent.agent_type == AgentType.CODE.value
        capabilities = agent.get_capabilities()
        assert 'generate_python_code' in capabilities
        assert 'generate_javascript_code' in capabilities

    def test_process_python_succeeds(self, agent):
        result = agent.process({'language': 'python'})
        assert result['language'] == 'python'
        assert 'code' in result
        assert 'wsde' in result
        wsde = result['wsde']
        assert wsde.content == result['code']
        assert wsde.metadata['language'] == 'python'

    def test_process_javascript_succeeds(self, agent):
        result = agent.process({'language': 'javascript'})
        assert result['language'] == 'javascript'
        wsde = result['wsde']
        assert wsde.metadata['language'] == 'javascript'

    def test_process_unsupported_language_raises_error(self, agent):
        with pytest.raises(ValueError):
            agent.process({'language': 'ruby'})

    @patch('devsynth.application.agents.multi_language_code.logger')
    def test_process_wsde_creation_error_logs_and_returns(self, mock_logger, agent):
        with patch.object(agent, 'create_wsde', side_effect=Exception('fail')):
            result = agent.process({'language': 'python'})
            mock_logger.error.assert_called_once()
            assert result['wsde'] is None
