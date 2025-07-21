import pytest
from unittest.mock import patch, MagicMock
from devsynth.application.llm.providers import AnthropicProvider, AnthropicConnectionError, AnthropicModelError
anthropic_available = pytest.mark.requires_resource('anthropic')


class TestAnthropicProvider:
    """Integration tests for the AnthropicProvider class.

ReqID: N/A"""

    @anthropic_available
    def test_generate_integration_succeeds(self):
        """Test that generate integration succeeds.

ReqID: N/A"""
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'content': [{'text':
                'This is a test response from the mocked Anthropic API'}]}
            mock_post.return_value = mock_response
            provider = AnthropicProvider({'api_key': 'test_key'})
            response = provider.generate('Hello, Anthropic!')
            assert isinstance(response, str)
            assert response == 'This is a test response from the mocked Anthropic API'
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert '/v1/messages' in call_args[0][0]
            assert call_args[1]['headers']['x-api-key'] == 'test_key'

    @anthropic_available
    def test_generate_with_context_integration_succeeds(self):
        """Test that generate with context integration succeeds.

ReqID: N/A"""
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'content': [{'text':
                'This is a context response'}]}
            mock_post.return_value = mock_response
            provider = AnthropicProvider({'api_key': 'test_key'})
            context = [{'role': 'system', 'content': 'You are helpful.'}, {
                'role': 'user', 'content': 'Hi'}]
            response = provider.generate_with_context('Tell me a joke', context
                )
            assert isinstance(response, str)
            assert response == 'This is a context response'
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            messages = kwargs['json']['messages']
            assert len(messages) == 3
            assert messages[-1]['content'] == 'Tell me a joke'

    @anthropic_available
    def test_get_embedding_integration_succeeds(self):
        """Test that get embedding integration succeeds.

ReqID: N/A"""
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'embedding': [0.1, 0.2, 0.3]}
            mock_post.return_value = mock_response
            provider = AnthropicProvider({'api_key': 'test_key'})
            embedding = provider.get_embedding('embed this')
            assert isinstance(embedding, list)
            assert embedding == [0.1, 0.2, 0.3]
            mock_post.assert_called_once()
            assert '/v1/embeddings' in mock_post.call_args[0][0]
            assert mock_post.call_args[1]['headers']['x-api-key'] == 'test_key'
