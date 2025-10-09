"""Unit tests for the LM Studio provider implementation."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from devsynth.application.llm.lmstudio_provider import (
    LMStudioConnectionError,
    LMStudioModelError,
    LMStudioProvider,
    _AttrForwarder,
    _LMStudioProxy,
    _NamespaceForwarder,
    _require_lmstudio,
    lmstudio,
)
from devsynth.exceptions import DevSynthError


class TestLMStudioProxy:
    """Test the LM Studio proxy and forwarding mechanisms."""

    @pytest.mark.fast
    def test_proxy_initialization(self):
        """Test that the proxy initializes correctly."""
        proxy = _LMStudioProxy()

        assert proxy._real is None
        assert hasattr(proxy, "llm")
        assert hasattr(proxy, "embedding_model")
        assert hasattr(proxy, "sync_api")
        assert isinstance(proxy.llm, _AttrForwarder)
        assert isinstance(proxy.sync_api, _NamespaceForwarder)

    @pytest.mark.fast
    def test_proxy_ensure_lazy_import(self):
        """Test that proxy defers importing until _ensure is called."""
        proxy = _LMStudioProxy()

        # Should not have imported yet
        assert proxy._real is None

        # Mock the import function to verify it's called
        with patch(
            "devsynth.application.llm.lmstudio_provider._require_lmstudio"
        ) as mock_require:
            mock_lmstudio_module = MagicMock()
            mock_require.return_value = mock_lmstudio_module

            result = proxy._ensure()

            assert result is mock_lmstudio_module
            assert proxy._real is mock_lmstudio_module
            mock_require.assert_called_once()

    @pytest.mark.fast
    def test_proxy_ensure_caching(self):
        """Test that proxy caches the imported module."""
        proxy = _LMStudioProxy()

        with patch(
            "devsynth.application.llm.lmstudio_provider._require_lmstudio"
        ) as mock_require:
            mock_lmstudio_module = MagicMock()
            mock_require.return_value = mock_lmstudio_module

            # Call _ensure twice
            result1 = proxy._ensure()
            result2 = proxy._ensure()

            # Should return the same instance and only call once
            assert result1 is result2
            assert result1 is mock_lmstudio_module
            mock_require.assert_called_once()

    @pytest.mark.fast
    def test_proxy_getattr_delegation(self):
        """Test that proxy delegates attribute access to the real module."""
        proxy = _LMStudioProxy()

        with patch(
            "devsynth.application.llm.lmstudio_provider._require_lmstudio"
        ) as mock_require:
            mock_lmstudio_module = MagicMock()
            mock_lmstudio_module.test_attr = "test_value"
            mock_require.return_value = mock_lmstudio_module

            # Access an attribute that doesn't exist on proxy
            result = proxy.test_attr

            assert result == "test_value"
            mock_require.assert_called_once()


class TestAttrForwarder:
    """Test the attribute forwarder mechanism."""

    @pytest.mark.fast
    def test_attr_forwarder_initialization(self):
        """Test that AttrForwarder initializes correctly."""
        proxy = _LMStudioProxy()
        forwarder = _AttrForwarder(proxy, "test_attr")

        assert forwarder._proxy is proxy
        assert forwarder._attr == "test_attr"

    @pytest.mark.fast
    def test_attr_forwarder_call(self):
        """Test that AttrForwarder forwards callable access."""
        proxy = _LMStudioProxy()
        forwarder = _AttrForwarder(proxy, "test_attr")

        with patch.object(proxy, "_ensure") as mock_ensure:
            mock_real_module = MagicMock()
            mock_attr = MagicMock()
            mock_attr.return_value = "test_result"
            mock_real_module.test_attr = mock_attr
            mock_ensure.return_value = mock_real_module

            result = forwarder("arg1", "arg2", key="value")

            assert result == "test_result"
            mock_attr.assert_called_once_with("arg1", "arg2", key="value")
            mock_ensure.assert_called_once()


class TestNamespaceForwarder:
    """Test the namespace forwarder mechanism."""

    @pytest.mark.fast
    def test_namespace_forwarder_initialization(self):
        """Test that NamespaceForwarder initializes correctly."""
        proxy = _LMStudioProxy()
        forwarder = _NamespaceForwarder(proxy, "sync_api")

        assert forwarder._proxy is proxy
        assert forwarder._ns_name == "sync_api"

    @pytest.mark.fast
    def test_namespace_forwarder_getattr(self):
        """Test that NamespaceForwarder forwards attribute access."""
        proxy = _LMStudioProxy()
        forwarder = _NamespaceForwarder(proxy, "sync_api")

        with patch.object(proxy, "_ensure") as mock_ensure:
            mock_real_module = MagicMock()
            mock_namespace = MagicMock()
            mock_namespace.test_method = "test_value"
            mock_real_module.sync_api = mock_namespace
            mock_ensure.return_value = mock_real_module

            result = forwarder.test_method

            assert result == "test_value"
            mock_ensure.assert_called_once()

    @pytest.mark.fast
    def test_namespace_forwarder_list_downloaded_models(self):
        """Test that NamespaceForwarder provides list_downloaded_models method."""
        proxy = _LMStudioProxy()
        forwarder = _NamespaceForwarder(proxy, "sync_api")

        with patch.object(proxy, "_ensure") as mock_ensure:
            mock_real_module = MagicMock()
            mock_namespace = MagicMock()
            mock_namespace.list_downloaded_models.return_value = ["model1", "model2"]
            mock_real_module.sync_api = mock_namespace
            mock_ensure.return_value = mock_real_module

            result = forwarder.list_downloaded_models()

            assert result == ["model1", "model2"]
            mock_namespace.list_downloaded_models.assert_called_once()

    @pytest.mark.fast
    def test_namespace_forwarder_configure_default_client(self):
        """Test that NamespaceForwarder provides configure_default_client method."""
        proxy = _LMStudioProxy()
        forwarder = _NamespaceForwarder(proxy, "sync_api")

        with patch.object(proxy, "_ensure") as mock_ensure:
            mock_real_module = MagicMock()
            mock_namespace = MagicMock()
            mock_namespace.configure_default_client.return_value = "configured"
            mock_real_module.sync_api = mock_namespace
            mock_ensure.return_value = mock_real_module

            result = forwarder.configure_default_client("client_config")

            assert result == "configured"
            mock_namespace.configure_default_client.assert_called_once_with(
                "client_config"
            )


class TestRequireLMStudio:
    """Test the lazy import function."""

    @pytest.mark.fast
    def test_require_lmstudio_success(self):
        """Test successful import of lmstudio module."""
        with patch.dict("sys.modules", {"lmstudio": MagicMock()}):
            result = _require_lmstudio()
            assert result is not None

    @pytest.mark.fast
    def test_require_lmstudio_import_error(self):
        """Test error handling when lmstudio module is not available."""
        with patch.dict("sys.modules", {}, clear=True):
            with patch(
                "builtins.__import__", side_effect=ImportError("Module not found")
            ):
                with pytest.raises(DevSynthError) as exc_info:
                    _require_lmstudio()

                assert "LMStudio support requires" in str(exc_info.value)
                assert "lmstudio" in str(exc_info.value)


class TestLMStudioProvider:
    """Test the LM Studio provider implementation."""

    @pytest.mark.fast
    def test_provider_initialization_default_config(self):
        """Test provider initialization with default configuration."""
        with patch(
            "devsynth.application.llm.lmstudio_provider.get_llm_settings"
        ) as mock_get_settings:
            mock_settings = {
                "lmstudio": {
                    "api_base": "http://127.0.0.1:1234",
                    "model": "local_model",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                }
            }
            mock_get_settings.return_value = mock_settings

            provider = LMStudioProvider()

            assert provider.api_base == "http://127.0.0.1:1234"
            assert provider.model == "local_model"
            assert provider.max_tokens is None  # Not set if not in config
            assert provider.temperature is None  # Not set if not in config
            # Check that _lmstudio is set
            assert hasattr(provider, "_lmstudio")
            mock_get_settings.assert_called_once()

    @pytest.mark.fast
    def test_provider_initialization_custom_config(self):
        """Test provider initialization with custom configuration."""
        custom_config = {
            "api_base": "http://custom:8080",
            "model": "custom-model",
            "max_tokens": 2000,
            "temperature": 0.8,
        }

        provider = LMStudioProvider(custom_config)

        assert provider.api_base == "http://custom:8080"
        assert provider.model == "custom-model"
        assert provider.max_tokens == 2000
        assert provider.temperature == 0.8

    @pytest.mark.fast
    def test_provider_complete_method(self):
        """Test the complete method functionality."""
        provider = LMStudioProvider()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Test response"
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = provider.complete("Test prompt")

            assert result == "Test response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.fast
    def test_provider_embed_method(self):
        """Test the embed method functionality."""
        provider = LMStudioProvider()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
            mock_client.embeddings.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = provider.embed(["Test text"])

            assert len(result) == 1
            assert result[0] == [0.1, 0.2, 0.3]
            mock_client.embeddings.create.assert_called_once()

    @pytest.mark.fast
    def test_provider_health_check_success(self):
        """Test successful health check."""
        provider = LMStudioProvider()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.list.return_value = ["model1", "model2"]
            mock_get_client.return_value = mock_client

            result = provider.health_check()

            assert result is True
            mock_client.models.list.assert_called_once()

    @pytest.mark.fast
    def test_provider_health_check_failure(self):
        """Test failed health check."""
        provider = LMStudioProvider()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_get_client.side_effect = Exception("Connection failed")

            result = provider.health_check()

            assert result is False

    @pytest.mark.fast
    def test_provider_get_client_method(self):
        """Test the _get_client method."""
        provider = LMStudioProvider()

        with patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio"
        ) as mock_lmstudio:
            mock_client = MagicMock()
            mock_lmstudio.llm.return_value = mock_client

            result = provider._get_client()

            assert result is mock_client
            mock_lmstudio.llm.assert_called_once()

    @pytest.mark.fast
    def test_provider_model_property(self):
        """Test the model property getter and setter."""
        provider = LMStudioProvider()

        # Test getter
        assert provider.model == "default-model"

        # Test setter
        provider.model = "new-model"
        assert provider.model == "new-model"

    @pytest.mark.fast
    def test_provider_available_models_property(self):
        """Test the available_models property."""
        provider = LMStudioProvider()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.list.return_value = ["model1", "model2", "model3"]
            mock_get_client.return_value = mock_client

            models = provider.available_models

            assert models == ["model1", "model2", "model3"]
            mock_client.models.list.assert_called_once()


class TestLMStudioExceptions:
    """Test LM Studio specific exceptions."""

    @pytest.mark.fast
    def test_connection_error_inheritance(self):
        """Test that LMStudioConnectionError inherits from DevSynthError."""
        error = LMStudioConnectionError("Connection failed")
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_model_error_inheritance(self):
        """Test that LMStudioModelError inherits from DevSynthError."""
        error = LMStudioModelError("Model not found")
        assert isinstance(error, DevSynthError)

    @pytest.mark.fast
    def test_connection_error_message(self):
        """Test LMStudioConnectionError message formatting."""
        error = LMStudioConnectionError("Connection timeout")
        assert str(error) == "Connection timeout"

    @pytest.mark.fast
    def test_model_error_message(self):
        """Test LMStudioModelError message formatting."""
        error = LMStudioModelError("Invalid model")
        assert str(error) == "Invalid model"


class TestModuleLevelProxy:
    """Test the module-level lmstudio proxy."""

    @pytest.mark.fast
    def test_module_level_proxy_exists(self):
        """Test that the module-level lmstudio proxy exists."""
        assert lmstudio is not None
        assert isinstance(lmstudio, _LMStudioProxy)

    @pytest.mark.fast
    def test_module_level_proxy_has_expected_attributes(self):
        """Test that the module-level proxy has expected attributes."""
        assert hasattr(lmstudio, "llm")
        assert hasattr(lmstudio, "embedding_model")
        assert hasattr(lmstudio, "sync_api")

        assert isinstance(lmstudio.llm, _AttrForwarder)
        assert isinstance(lmstudio.sync_api, _NamespaceForwarder)
