"""Shared fixtures and stubs for tests under :mod:`tests.unit.testing`."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Callable, Iterable, Sequence

import pytest

CoverageHook = Callable[[Path], None]

_CONFIG_MODULE = ModuleType("devsynth.config")
_SETTINGS_MODULE = ModuleType("devsynth.config.settings")


def _ensure_path_exists(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


class _StubSettings(SimpleNamespace):
    """Lightweight stand-in for ``devsynth.config.settings.Settings``."""

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)


def _make_default_settings() -> _StubSettings:
    """Return deterministic default settings for tests."""

    return _StubSettings(
        tls_verify=True,
        tls_cert_file=None,
        tls_key_file=None,
        tls_ca_file=None,
        provider_max_retries=3,
        provider_initial_delay=1.0,
        provider_exponential_base=2.0,
        provider_max_delay=60.0,
        provider_jitter=True,
        provider_retry_metrics=True,
        provider_retry_conditions="",
        provider_fallback_enabled=True,
        provider_fallback_order="openai,lmstudio,stub",
        provider_circuit_breaker_enabled=True,
        provider_failure_threshold=5,
        provider_recovery_timeout=60.0,
        provider_type="stub",
        lm_studio_endpoint="http://localhost",
        llm_provider="stub",
        llm_model="stub-model",
        llm_temperature=0.7,
        llm_auto_select_model=True,
        openai_api_key=None,
        openai_model="gpt-4",
        access_token=None,
        llm_api_base="http://127.0.0.1:1234",
        llm_max_tokens=1024,
        llm_timeout=60,
    )


def _stub_get_settings(*_, **__) -> _StubSettings:
    settings = _make_default_settings()

    env_provider = os.environ.get("DEVSYNTH_LLM_PROVIDER")
    if env_provider:
        settings.llm_provider = env_provider

    env_api_base = os.environ.get("DEVSYNTH_LLM_API_BASE")
    if env_api_base:
        settings.llm_api_base = env_api_base

    env_max_tokens = os.environ.get("DEVSYNTH_LLM_MAX_TOKENS")
    if env_max_tokens and env_max_tokens.isdigit():
        settings.llm_max_tokens = int(env_max_tokens)

    env_timeout = os.environ.get("DEVSYNTH_LLM_TIMEOUT")
    if env_timeout:
        try:
            settings.llm_timeout = int(env_timeout)
        except ValueError:
            pass

    env_access_token = os.environ.get("DEVSYNTH_ACCESS_TOKEN")
    if env_access_token is not None:
        settings.access_token = env_access_token

    return settings


def _stub_get_llm_settings(*_, **__) -> dict[str, object]:
    settings = _stub_get_settings()
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "auto_select_model": settings.llm_auto_select_model,
        "api_base": settings.llm_api_base,
        "max_tokens": settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
    }


_SETTINGS_MODULE.ensure_path_exists = _ensure_path_exists  # type: ignore[attr-defined]
_SETTINGS_MODULE.get_settings = _stub_get_settings  # type: ignore[attr-defined]
_SETTINGS_MODULE.get_llm_settings = _stub_get_llm_settings  # type: ignore[attr-defined]
_CONFIG_MODULE.settings = _SETTINGS_MODULE  # type: ignore[attr-defined]
sys.modules.setdefault("devsynth.config", _CONFIG_MODULE)
sys.modules.setdefault("devsynth.config.settings", _SETTINGS_MODULE)


@pytest.fixture(autouse=True)
def stub_devsynth_config(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Reinstall the lightweight ``devsynth.config`` stub for each test."""

    monkeypatch.setitem(sys.modules, "devsynth.config", _CONFIG_MODULE)
    monkeypatch.setitem(sys.modules, "devsynth.config.settings", _SETTINGS_MODULE)
    return _CONFIG_MODULE


@pytest.fixture
def coverage_stub_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., SimpleNamespace]:
    """Provide a factory that installs a fake ``coverage.Coverage`` implementation."""

    def factory(
        *,
        measured_files: Sequence[str] | None,
        on_html: CoverageHook | None = None,
        on_json: CoverageHook | None = None,
        on_load: Callable[["FakeCoverage"], None] | None = None,
    ) -> SimpleNamespace:
        html_calls: list[Path] = []
        json_calls: list[Path] = []
        instances: list["FakeCoverage"] = []

        class FakeCoverage:
            """Test double mimicking the ``coverage.Coverage`` API surface."""

            def __init__(self, data_file: str) -> None:
                self.data_file = data_file
                instances.append(self)

            def load(self) -> None:
                if on_load is not None:
                    on_load(self)

            def get_data(self) -> SimpleNamespace:
                files: Iterable[str] = [] if measured_files is None else measured_files
                return SimpleNamespace(measured_files=lambda: list(files))

            def html_report(self, directory: str) -> None:
                path = Path(directory)
                html_calls.append(path)
                if on_html is not None:
                    on_html(path)

            def json_report(self, outfile: str) -> None:
                path = Path(outfile)
                json_calls.append(path)
                if on_json is not None:
                    on_json(path)

        module = ModuleType("coverage")
        module.Coverage = FakeCoverage  # type: ignore[attr-defined]
        module.FakeCoverage = FakeCoverage  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "coverage", module)

        return SimpleNamespace(
            html_calls=html_calls,
            json_calls=json_calls,
            instances=instances,
            module=module,
        )

    return factory
