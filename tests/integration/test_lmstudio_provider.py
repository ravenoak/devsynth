import os
import json
import pytest
import tempfile
import requests
from unittest.mock import patch, MagicMock
from devsynth.application.llm.lmstudio_provider import LMStudioProvider, LMStudioConnectionError, LMStudioModelError
lmstudio_available = pytest.mark.requires_resource('lmstudio')


class TestLMStudioProvider:
    """Tests for the LMStudioProvider class.

ReqID: N/A"""

    def test_init_with_default_config_succeeds(self):
        """Test initialization with default configuration.

ReqID: N/A"""
        with patch(
            'devsynth.application.llm.lmstudio_provider.get_llm_settings'
            ) as mock_settings, patch(
            'devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models'
            ) as mock_list:
            mock_settings.return_value = {'api_base':
                'http://localhost:1234/v1', 'model': None, 'max_tokens': 
                1024, 'temperature': 0.7, 'auto_select_model': True}
            mock_list.return_value = [{'id': 'test_model', 'name':
                'Test Model'}]
            provider = LMStudioProvider()
            assert provider.model == 'test_model'
            assert provider.api_base == 'http://localhost:1234/v1'
            assert provider.max_tokens == 1024

    def test_init_with_specified_model_succeeds(self):
        """Test initialization with a specified model.

ReqID: N/A"""
        provider = LMStudioProvider({'model': 'specified_model'})
        assert provider.model == 'specified_model'

    def test_init_with_connection_error_succeeds(self):
        """Test initialization when LM Studio is not available.

ReqID: N/A"""
        with patch(
            'devsynth.application.llm.lmstudio_provider.get_llm_settings'
            ) as mock_settings, patch(
            'devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models'
            ) as mock_list:
            mock_settings.return_value = {'api_base':
                'http://localhost:1234/v1', 'model': None, 'max_tokens': 
                1024, 'temperature': 0.7, 'auto_select_model': True}
            mock_list.side_effect = LMStudioConnectionError('Connection error')
            provider = LMStudioProvider()
            assert provider.model == 'local_model'

    def test_list_available_models_error_fails(self):
        """Test listing available models when the API call fails.

ReqID: N/A"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = 'Internal server error'
            mock_get.return_value = mock_response
            provider = LMStudioProvider({'auto_select_model': False})
            with pytest.raises(LMStudioConnectionError):
                provider.list_available_models()

    @lmstudio_available
    def test_list_available_models_integration_succeeds(self):
        """Integration test for listing available models from LM Studio.

ReqID: N/A"""
        provider = LMStudioProvider()
        models = provider.list_available_models()
        assert isinstance(models, list)
        if models:
            assert 'id' in models[0]

    @lmstudio_available
    def test_generate_integration_succeeds(self):
        """Integration test for generating text from LM Studio.

ReqID: N/A"""
        with patch(
            'devsynth.application.llm.lmstudio_provider.get_llm_settings'
            ) as mock_settings, patch(
            'devsynth.application.llm.lmstudio_provider.requests.post'
            ) as mock_post, patch(
            'devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models'
            ) as mock_list:
            mock_settings.return_value = {'api_base':
                'http://localhost:1234/v1', 'model': 'test_model',
                'max_tokens': 1024, 'temperature': 0.7, 'auto_select_model':
                False}
            mock_list.return_value = [{'id': 'test_model', 'name':
                'Test Model'}]
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'choices': [{'message': {
                'content':
                'This is a test response from the mocked LM Studio API'}}]}
            mock_post.return_value = mock_response
            provider = LMStudioProvider()
            response = provider.generate('Hello, how are you?')
            assert isinstance(response, str)
            assert response == 'This is a test response from the mocked LM Studio API'
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0
                ] == 'http://localhost:1234/v1/chat/completions'
            assert 'Hello, how are you?' in call_args[1]['data']

    def test_generate_with_connection_error_succeeds(self):
        """Test generating text when LM Studio is not available.

ReqID: N/A"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.RequestException(
                'Connection error')
            provider = LMStudioProvider({'auto_select_model': False})
            with pytest.raises(LMStudioConnectionError):
                provider.generate('Hello, how are you?')

    def test_generate_with_invalid_response_returns_expected_result(self):
        """Test generating text when LM Studio returns an invalid response.

ReqID: N/A"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'invalid': 'response'}
            mock_post.return_value = mock_response
            provider = LMStudioProvider({'auto_select_model': False})
            with pytest.raises(LMStudioModelError):
                provider.generate('Hello, how are you?')

    @lmstudio_available
    def test_generate_with_context_integration_succeeds(self):
        """Integration test for generating text with context from LM Studio.

ReqID: N/A"""
        with patch(
            'devsynth.application.llm.lmstudio_provider.get_llm_settings'
            ) as mock_settings, patch(
            'devsynth.application.llm.lmstudio_provider.requests.post'
            ) as mock_post, patch(
            'devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models'
            ) as mock_list:
            mock_settings.return_value = {'api_base':
                'http://localhost:1234/v1', 'model': 'test_model',
                'max_tokens': 1024, 'temperature': 0.7, 'auto_select_model':
                False}
            mock_list.return_value = [{'id': 'test_model', 'name':
                'Test Model'}]
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'choices': [{'message': {
                'content':
                'This is a test response with context from the mocked LM Studio API'
                }}]}
            mock_post.return_value = mock_response
            provider = LMStudioProvider()
            context = [{'role': 'system', 'content':
                'You are a helpful assistant.'}, {'role': 'user', 'content':
                'Hello, who are you?'}, {'role': 'assistant', 'content':
                "I'm an AI assistant. How can I help you?"}]
            response = provider.generate_with_context(
                'Tell me more about yourself.', context)
            assert isinstance(response, str)
            assert response == 'This is a test response with context from the mocked LM Studio API'
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0
                ] == 'http://localhost:1234/v1/chat/completions'
            data = json.loads(call_args[1]['data'])
            assert len(data['messages']) == 4
            assert data['messages'][-1]['content'
                ] == 'Tell me more about yourself.'


if __name__ == '__main__':
    pytest.main(['-v', 'test_lmstudio_provider.py'])
