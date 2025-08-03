import sys
import types
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
import devsynth.domain.interfaces.llm
spec = importlib.util.spec_from_file_location('devsynth.application.llm.offline_provider', ROOT / 'src/devsynth/application/llm/offline_provider.py')
offline_provider = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = offline_provider
spec.loader.exec_module(offline_provider)
OfflineProvider = offline_provider.OfflineProvider

@pytest.mark.medium
def test_offline_provider_fallback_succeeds() -> None:
    """Test that offline provider fallback succeeds.

ReqID: N/A"""
    provider = OfflineProvider()
    assert provider.generate('hello') == '[offline] hello'
    assert provider.get_embedding('hello') == provider.get_embedding('hello')

@pytest.mark.medium
def test_offline_provider_loads_local_model_succeeds(tmp_path, monkeypatch) -> None:
    """Test that offline provider loads local model succeeds.

ReqID: N/A"""
    called = {}

    def fake_model_from_pretrained(path, *_, **__):
        called['model_path'] = path

        class DummyModel:

            def generate(self, **_):
                return [[0]]
        return DummyModel()

    def fake_tokenizer_from_pretrained(path, *_, **__):
        called['tokenizer_path'] = path

        class DummyTokenizer:

            def __call__(self, text, return_tensors=None):
                called['input_text'] = text
                return {}

            def decode(self, ids, skip_special_tokens=True):
                return 'Hello world'
        return DummyTokenizer()
    FakeModelCls = types.SimpleNamespace(from_pretrained=staticmethod(fake_model_from_pretrained))
    FakeTokCls = types.SimpleNamespace(from_pretrained=staticmethod(fake_tokenizer_from_pretrained))

    class DummyTorch:

        def no_grad(self):

            class Ctx:

                def __enter__(self):
                    return None

                def __exit__(self, exc_type, exc, tb):
                    pass
            return Ctx()
    monkeypatch.setattr(offline_provider, 'AutoModelForCausalLM', FakeModelCls)
    monkeypatch.setattr(offline_provider, 'AutoTokenizer', FakeTokCls)
    monkeypatch.setattr(offline_provider, 'torch', DummyTorch())
    provider = OfflineProvider({'offline_provider': {'model_path': str(tmp_path)}})
    result = provider.generate('Hello')
    assert result == 'Hello world'
    assert called['model_path'] == str(tmp_path)
    assert called['tokenizer_path'] == str(tmp_path)

@pytest.mark.medium
def test_generate_with_context_succeeds() -> None:
    """Test the generate_with_context method.

ReqID: N/A"""
    provider = OfflineProvider()
    context = [{'role': 'user', 'content': 'What is the capital of France?'}, {'role': 'assistant', 'content': 'The capital of France is Paris.'}]
    result = provider.generate_with_context('Tell me more about it.', context)
    expected = '[offline] What is the capital of France? The capital of France is Paris. Tell me more about it.'
    assert result == expected

@pytest.mark.medium
def test_generate_with_empty_context_succeeds() -> None:
    """Test generate_with_context with empty context.

ReqID: N/A"""
    provider = OfflineProvider()
    result = provider.generate_with_context('Hello', [])
    assert result == '[offline] Hello'

@pytest.mark.medium
def test_generate_with_empty_prompt_succeeds() -> None:
    """Test generate with empty prompt.

ReqID: N/A"""
    provider = OfflineProvider()
    result = provider.generate('')
    assert result == '[offline] '

@pytest.mark.medium
def test_get_embedding_consistency_succeeds() -> None:
    """Test that embeddings are consistent for the same input.

ReqID: N/A"""
    provider = OfflineProvider()
    text = 'This is a test'
    embedding1 = provider.get_embedding(text)
    embedding2 = provider.get_embedding(text)
    assert embedding1 == embedding2
    assert len(embedding1) == 8

@pytest.mark.medium
def test_get_embedding_different_inputs_succeeds() -> None:
    """Test that embeddings are different for different inputs.

ReqID: N/A"""
    provider = OfflineProvider()
    embedding1 = provider.get_embedding('text1')
    embedding2 = provider.get_embedding('text2')
    assert embedding1 != embedding2

@pytest.mark.medium
def test_model_loading_error_fails(tmp_path, monkeypatch) -> None:
    """Test error handling when model loading fails.

ReqID: N/A"""

    def mock_from_pretrained(*args, **kwargs):
        raise ValueError('Failed to load model')
    monkeypatch.setattr(offline_provider, 'AutoTokenizer', MagicMock(from_pretrained=mock_from_pretrained))
    monkeypatch.setattr(offline_provider, 'AutoModelForCausalLM', MagicMock())
    mock_logger = MagicMock()
    with patch.object(offline_provider, 'DevSynthLogger', return_value=mock_logger):
        provider = OfflineProvider({'offline_provider': {'model_path': str(tmp_path)}})
        mock_logger.error.assert_called_once()
        assert 'Failed to load model' in mock_logger.error.call_args[0][0]
        result = provider.generate('test')
        assert result == '[offline] test'