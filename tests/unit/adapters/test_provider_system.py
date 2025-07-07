import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
import httpx
import requests

from devsynth.adapters import provider_system
from devsynth.adapters.provider_system import (
    ProviderError, ProviderFactory, BaseProvider, 
    OpenAIProvider, LMStudioProvider, FallbackProvider,
    get_env_or_default, get_provider_config
)
from devsynth.fallback import retry_with_exponential_backoff


def test_embed_success():
    provider = MagicMock()
    provider.embed.return_value = [[1.0, 2.0]]
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = provider_system.embed(
            "text", provider_type="lm_studio", fallback=False
        )
        assert result == [[1.0, 2.0]]
        provider.embed.assert_called_once()


def test_embed_error():
    provider = MagicMock()
    provider.embed.side_effect = ProviderError("fail")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.embed("text", provider_type="lm_studio", fallback=False)


def test_aembed_success():
    provider = MagicMock()
    provider.aembed = AsyncMock(return_value=[[3.0, 4.0]])

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            result = await provider_system.aembed(
                "text", provider_type="lm_studio", fallback=False
            )
            assert result == [[3.0, 4.0]]
            provider.aembed.assert_awaited_once()

    asyncio.run(run_test())


def test_aembed_error():
    provider = MagicMock()
    provider.aembed = AsyncMock(side_effect=ProviderError("boom"))

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            with pytest.raises(ProviderError):
                await provider_system.aembed(
                    "text", provider_type="lm_studio", fallback=False
                )

    asyncio.run(run_test())


def test_complete_success():
    provider = MagicMock()
    provider.complete.return_value = "Completed text"
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = provider_system.complete(
            "prompt", system_prompt="system", provider_type="openai", fallback=False
        )
        assert result == "Completed text"
        provider.complete.assert_called_once_with(
            prompt="prompt", system_prompt="system", temperature=0.7, max_tokens=2000
        )


def test_complete_error():
    provider = MagicMock()
    provider.complete.side_effect = ProviderError("completion failed")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.complete(
                "prompt", provider_type="openai", fallback=False
            )


def test_acomplete_success():
    provider = MagicMock()
    provider.acomplete = AsyncMock(return_value="Async completed text")

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            result = await provider_system.acomplete(
                "prompt", system_prompt="system", provider_type="openai", fallback=False
            )
            assert result == "Async completed text"
            provider.acomplete.assert_awaited_once_with(
                prompt="prompt", system_prompt="system", temperature=0.7, max_tokens=2000
            )

    asyncio.run(run_test())


def test_acomplete_error():
    provider = MagicMock()
    provider.acomplete = AsyncMock(side_effect=ProviderError("async completion failed"))

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            with pytest.raises(ProviderError):
                await provider_system.acomplete(
                    "prompt", provider_type="openai", fallback=False
                )

    asyncio.run(run_test())


def test_provider_factory_create_provider():
    with patch.object(provider_system, "get_provider_config") as mock_config:
        # Mock the provider classes to avoid actual initialization
        with patch.object(provider_system, "OpenAIProvider") as mock_openai:
            with patch.object(provider_system, "LMStudioProvider") as mock_lmstudio:
                # Configure mocks
                mock_openai_instance = MagicMock(spec=OpenAIProvider)
                mock_openai.return_value = mock_openai_instance

                mock_lmstudio_instance = MagicMock(spec=LMStudioProvider)
                mock_lmstudio.return_value = mock_lmstudio_instance

                # Test OpenAI provider creation
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {
                        "api_key": "test_key",
                        "model": "gpt-4",
                        "base_url": "https://api.openai.com/v1",
                    },
                    "retry": {
                        "max_retries": 3,
                        "initial_delay": 1.0,
                        "exponential_base": 2.0,
                        "max_delay": 60.0,
                        "jitter": True,
                    },
                }
                factory = ProviderFactory()
                provider = factory.create_provider("openai")
                mock_openai.assert_called_once()
                assert provider is mock_openai_instance

                # Reset mocks
                mock_openai.reset_mock()

                # Test LM Studio provider creation
                mock_config.return_value = {
                    "default_provider": "lm_studio",
                    "lm_studio": {
                        "endpoint": "http://test-endpoint",
                        "model": "default",
                    },
                    "retry": {
                        "max_retries": 3,
                        "initial_delay": 1.0,
                        "exponential_base": 2.0,
                        "max_delay": 60.0,
                        "jitter": True,
                    },
                }
                provider = factory.create_provider("lm_studio")
                mock_lmstudio.assert_called_once()
                assert provider is mock_lmstudio_instance

                # Reset mocks
                mock_openai.reset_mock()

                # Test default provider creation
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {
                        "api_key": "default_key",
                        "model": "gpt-3.5-turbo",
                        "base_url": "https://api.openai.com/v1",
                    },
                    "retry": {
                        "max_retries": 3,
                        "initial_delay": 1.0,
                        "exponential_base": 2.0,
                        "max_delay": 60.0,
                        "jitter": True,
                    },
                }
                provider = factory.create_provider()
                mock_openai.assert_called_once()
                assert provider is mock_openai_instance


def test_get_provider():
    with patch.object(ProviderFactory, "create_provider") as mock_create:
        # Test with fallback=True
        mock_create.return_value = MagicMock(spec=OpenAIProvider)
        provider = provider_system.get_provider(provider_type="openai", fallback=True)
        assert isinstance(provider, FallbackProvider)

        # Test with fallback=False
        provider = provider_system.get_provider(provider_type="openai", fallback=False)
        assert not isinstance(provider, FallbackProvider)
        mock_create.assert_called_with("openai")


def test_base_provider_methods():
    # Test that abstract methods raise NotImplementedError
    provider = BaseProvider()

    with pytest.raises(NotImplementedError):
        provider.complete("test")

    with pytest.raises(NotImplementedError):
        provider.embed("test")

    with pytest.raises(NotImplementedError):
        asyncio.run(provider.acomplete("test"))

    with pytest.raises(NotImplementedError):
        asyncio.run(provider.aembed("test"))


@pytest.mark.parametrize("provider_class,config", [
    (OpenAIProvider, {"api_key": "test_key", "model": "gpt-4"}),
    (LMStudioProvider, {"endpoint": "http://test-endpoint"}),
])
def test_provider_initialization(provider_class, config):
    provider = provider_class(**config)
    assert provider is not None

    # Test retry decorator
    retry_decorator = provider.get_retry_decorator()
    assert callable(retry_decorator)


def test_fallback_provider():
    # Create mock providers
    provider1 = MagicMock(spec=BaseProvider)
    provider2 = MagicMock(spec=BaseProvider)

    # Configure the first provider to fail, second to succeed
    provider1.complete.side_effect = ProviderError("Provider 1 failed")
    provider2.complete.return_value = "Success from provider 2"

    # Create fallback provider with the mock providers
    fallback = FallbackProvider(providers=[provider1, provider2])

    # Test complete method with fallback
    result = fallback.complete("test prompt")
    assert result == "Success from provider 2"
    provider1.complete.assert_called_once()
    provider2.complete.assert_called_once()

    # Test when all providers fail
    provider2.complete.side_effect = ProviderError("Provider 2 failed")
    with pytest.raises(ProviderError):
        fallback.complete("test prompt")


def test_get_env_or_default():
    """Test the get_env_or_default function."""
    # Test with environment variable set
    with patch.dict('os.environ', {'TEST_VAR': 'test_value'}):
        assert get_env_or_default('TEST_VAR', 'default') == 'test_value'

    # Test with environment variable not set
    with patch.dict('os.environ', {}, clear=True):
        assert get_env_or_default('TEST_VAR', 'default') == 'default'

    # Test with environment variable not set and no default
    with patch.dict('os.environ', {}, clear=True):
        assert get_env_or_default('TEST_VAR') is None


def test_get_provider_config():
    """Test the get_provider_config function."""
    # Clear the LRU cache to ensure we get fresh results
    get_provider_config.cache_clear()

    # Test with environment variables set
    env_vars = {
        'DEVSYNTH_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test_key',
        'OPENAI_MODEL': 'gpt-4',
        'LM_STUDIO_ENDPOINT': 'http://test-endpoint'
    }

    with patch.dict('os.environ', env_vars, clear=True):
        config = get_provider_config()
        assert config['default_provider'] == 'openai'
        assert config['openai']['api_key'] == 'test_key'
        assert config['openai']['model'] == 'gpt-4'
        assert config['lm_studio']['endpoint'] == 'http://test-endpoint'

    # Clear the LRU cache again for the next test
    get_provider_config.cache_clear()

    # Test with minimal environment variables
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}, clear=True):
        config = get_provider_config()
        assert config['default_provider'] == 'openai'  # Default provider
        assert config['openai']['api_key'] == 'test_key'
        assert 'model' in config['openai']  # Should have default value


@patch('requests.post')
def test_openai_provider_complete(mock_post):
    """Test the complete method of OpenAIProvider."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Test completion'}}]
    }
    mock_post.return_value = mock_response

    # Create provider and test complete method
    provider = OpenAIProvider(api_key='test_key', model='gpt-4')
    result = provider.complete('Test prompt', system_prompt='System prompt')

    # Verify result
    assert result == 'Test completion'

    # Verify API call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == 'https://api.openai.com/v1/chat/completions'
    assert kwargs['headers']['Authorization'] == 'Bearer test_key'
    assert kwargs['json']['model'] == 'gpt-4'
    assert kwargs['json']['messages'][0]['content'] == 'System prompt'
    assert kwargs['json']['messages'][1]['content'] == 'Test prompt'


@patch('requests.post')
def test_openai_provider_complete_error(mock_post):
    """Test error handling in the complete method of OpenAIProvider."""
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': {'message': 'Bad request'}}
    mock_post.return_value = mock_response

    # Create provider and test complete method
    provider = OpenAIProvider(api_key='test_key', model='gpt-4')

    # Verify error handling
    with pytest.raises(ProviderError) as excinfo:
        provider.complete('Test prompt')

    assert 'Bad request' in str(excinfo.value)


@patch('requests.post')
def test_openai_provider_complete_retry(mock_post):
    """Test retry mechanism in the complete method of OpenAIProvider."""
    # Mock the retry_with_exponential_backoff function
    with patch('devsynth.adapters.provider_system.retry_with_exponential_backoff') as mock_retry:
        # Set up mock to return a function that returns the input function
        mock_retry.return_value = lambda func: func

        # Mock responses for retry
        error_response = MagicMock()
        error_response.status_code = 429  # Too many requests
        error_response.json.return_value = {'error': {'message': 'Rate limit exceeded'}}
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Client Error")

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'choices': [{'message': {'content': 'Test completion'}}]
        }

        # Set up mock to fail first, then succeed
        mock_post.side_effect = [error_response, success_response]

        # Create provider
        provider = OpenAIProvider(api_key='test_key', model='gpt-4')

        # We'll need to handle the exception ourselves since we've mocked the retry decorator
        try:
            provider.complete('Test prompt')
        except ProviderError:
            # Reset the mock to return success on next call
            mock_post.side_effect = [success_response]
            # Try again
            result = provider.complete('Test prompt')
            assert result == 'Test completion'

        # Verify retry was called with correct parameters
        assert mock_retry.call_count >= 1
        # Check that at least one call had the correct parameters
        retry_calls_with_correct_params = [
            call for call in mock_retry.call_args_list 
            if call[1].get('retryable_exceptions') == (requests.exceptions.RequestException,)
        ]
        assert len(retry_calls_with_correct_params) >= 1


@patch('httpx.AsyncClient.post')
def test_openai_provider_acomplete(mock_post):
    """Test the acomplete method of OpenAIProvider."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Async test completion'}}]
    }
    mock_post.return_value = mock_response

    # Create provider
    provider = OpenAIProvider(api_key='test_key', model='gpt-4')

    # Define async test function
    async def run_test():
        result = await provider.acomplete('Test prompt', system_prompt='System prompt')

        # Verify result
        assert result == 'Async test completion'

        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == 'https://api.openai.com/v1/chat/completions'
        assert kwargs['headers']['Authorization'] == 'Bearer test_key'
        assert kwargs['json']['model'] == 'gpt-4'
        assert kwargs['json']['messages'][0]['content'] == 'System prompt'
        assert kwargs['json']['messages'][1]['content'] == 'Test prompt'

    # Run the async test
    asyncio.run(run_test())


@patch('requests.post')
def test_openai_provider_embed(mock_post):
    """Test the embed method of OpenAIProvider."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [{'embedding': [0.1, 0.2, 0.3]}]
    }
    mock_post.return_value = mock_response

    # Create provider and test embed method
    provider = OpenAIProvider(api_key='test_key', model='gpt-4')
    result = provider.embed('Test text')

    # Verify result
    assert result == [[0.1, 0.2, 0.3]]

    # Verify API call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == 'https://api.openai.com/v1/embeddings'
    assert kwargs['headers']['Authorization'] == 'Bearer test_key'
    assert kwargs['json']['input'] == ['Test text']


@patch('requests.post')
def test_lmstudio_provider_complete(mock_post):
    """Test the complete method of LMStudioProvider."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'LM Studio completion'}}]
    }
    mock_post.return_value = mock_response

    # Create provider and test complete method
    provider = LMStudioProvider(endpoint='http://test-endpoint')
    result = provider.complete('Test prompt', system_prompt='System prompt')

    # Verify result
    assert result == 'LM Studio completion'

    # Verify API call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == 'http://test-endpoint/v1/chat/completions'
    assert kwargs['json']['messages'][0]['content'] == 'System prompt'
    assert kwargs['json']['messages'][1]['content'] == 'Test prompt'


def test_fallback_provider_async_methods():
    """Test the async methods of FallbackProvider."""
    # Create mock providers
    provider1 = MagicMock(spec=BaseProvider)
    provider2 = MagicMock(spec=BaseProvider)

    # Configure async methods
    provider1.acomplete = AsyncMock(side_effect=ProviderError("Provider 1 failed"))
    provider2.acomplete = AsyncMock(return_value="Async success from provider 2")

    provider1.aembed = AsyncMock(side_effect=ProviderError("Provider 1 failed"))
    provider2.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

    # Create fallback provider
    fallback = FallbackProvider(providers=[provider1, provider2])

    # Define async test function
    async def run_test():
        # Test acomplete method
        result = await fallback.acomplete("test prompt")
        assert result == "Async success from provider 2"
        provider1.acomplete.assert_awaited_once()
        provider2.acomplete.assert_awaited_once()

        # Test aembed method
        result = await fallback.aembed("test text")
        assert result == [[0.1, 0.2, 0.3]]
        provider1.aembed.assert_awaited_once()
        provider2.aembed.assert_awaited_once()

        # Test when all providers fail
        provider2.acomplete.side_effect = ProviderError("Provider 2 failed")
        with pytest.raises(ProviderError):
            await fallback.acomplete("test prompt")

    # Run the async test
    asyncio.run(run_test())


def test_provider_with_empty_inputs():
    """Test providers with empty inputs."""
    # Test OpenAI provider
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Empty prompt response'}}]
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider(api_key='test_key')
        result = provider.complete("")
        assert result == 'Empty prompt response'

        # Verify API call with empty prompt
        args, kwargs = mock_post.call_args
        assert kwargs['json']['messages'][0]['content'] == ""

    # Test LM Studio provider
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Empty prompt response'}}]
        }
        mock_post.return_value = mock_response

        provider = LMStudioProvider()
        result = provider.complete("")
        assert result == 'Empty prompt response'
