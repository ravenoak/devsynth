"""Benchmarks for provider factory creation. ReqID: PERF-03"""

from devsynth.adapters.providers.provider_factory import ProviderFactory, ProviderType


def _config_with_openai_key():
    return {
        "default_provider": "openai",
        "openai": {
            "api_key": "test",
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1",
        },
        "lmstudio": {"endpoint": "http://localhost:1234", "model": "default"},
    }


def _config_without_openai_key():
    return {
        "default_provider": "openai",
        "openai": {
            "api_key": None,
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1",
        },
        "lmstudio": {"endpoint": "http://localhost:1234", "model": "default"},
    }


def test_provider_factory_openai_benchmark(benchmark, monkeypatch):
    """Benchmark OpenAI provider creation. ReqID: PERF-03"""
    monkeypatch.setattr(
        "devsynth.adapters.provider_system.get_provider_config", _config_with_openai_key
    )
    benchmark(lambda: ProviderFactory.create_provider(ProviderType.OPENAI.value))


def test_provider_factory_fallback_benchmark(benchmark, monkeypatch):
    """Benchmark default provider fallback creation. ReqID: PERF-03"""
    monkeypatch.setattr(
        "devsynth.adapters.provider_system.get_provider_config",
        _config_without_openai_key,
    )
    benchmark(lambda: ProviderFactory.create_provider())
