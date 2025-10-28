from __future__ import annotations

import asyncio
import sys
import types
from collections import deque
from types import MethodType, SimpleNamespace
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

try:  # pragma: no cover - guard optional dependency in tests
    import jsonschema  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    jsonschema_stub = types.ModuleType("jsonschema")
    sys.modules["jsonschema"] = jsonschema_stub

try:  # pragma: no cover - guard optional dependency in tests
    import toml  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    toml_stub = types.ModuleType("toml")
    toml_stub.TomlDecodeError = Exception  # type: ignore[attr-defined]
    toml_stub.load = lambda *_args, **_kwargs: {}  # type: ignore[attr-defined]
    sys.modules["toml"] = toml_stub

try:  # pragma: no cover - guard optional dependency in tests
    import yaml  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    yaml_stub = types.ModuleType("yaml")
    sys.modules["yaml"] = yaml_stub

try:  # pragma: no cover - guard optional dependency in tests
    import pydantic  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    pydantic_stub = types.ModuleType("pydantic")

    class _ValidationError(Exception):
        pass

    pydantic_stub.ValidationError = _ValidationError  # type: ignore[attr-defined]

    def _Field(
        *args, default=None, **_kwargs
    ):  # noqa: ANN001 - mimic pydantic signature
        return default

    class _FieldValidationInfo:  # noqa: D401 - simple placeholder
        """Placeholder for FieldValidationInfo."""

        pass

    pydantic_stub.Field = _Field  # type: ignore[attr-defined]
    pydantic_stub.FieldValidationInfo = _FieldValidationInfo  # type: ignore[attr-defined]

    def _field_validator(*_names, **_kwargs):
        def _decorator(func):
            return func

        return _decorator

    pydantic_stub.field_validator = _field_validator  # type: ignore[attr-defined]
    sys.modules["pydantic"] = pydantic_stub

    import dataclasses as _dataclasses

    pydantic_dataclasses = types.ModuleType("pydantic.dataclasses")
    pydantic_dataclasses.dataclass = _dataclasses.dataclass  # type: ignore[attr-defined]
    sys.modules["pydantic.dataclasses"] = pydantic_dataclasses

try:  # pragma: no cover - guard optional dependency in tests
    import pydantic_settings  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    pydantic_settings_stub = types.ModuleType("pydantic_settings")

    class _BaseSettings:
        model_config: dict[str, object] | None = None

        def __init__(self, **_kwargs):
            return None

    pydantic_settings_stub.BaseSettings = _BaseSettings  # type: ignore[attr-defined]
    pydantic_settings_stub.SettingsConfigDict = dict  # type: ignore[attr-defined]
    sys.modules["pydantic_settings"] = pydantic_settings_stub

try:  # pragma: no cover - guard optional dependency in tests
    import typing_extensions  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    typing_extensions_stub = types.ModuleType("typing_extensions")
    from typing import Self as _StdSelf
    from typing import TypedDict as _StdTypedDict

    typing_extensions_stub.TypedDict = _StdTypedDict  # type: ignore[attr-defined]
    typing_extensions_stub.Self = _StdSelf  # type: ignore[attr-defined]
    sys.modules["typing_extensions"] = typing_extensions_stub
else:  # pragma: no cover - augment existing module if needed
    from typing import Self as _StdSelf

    if not hasattr(typing_extensions, "Self"):
        typing_extensions.Self = _StdSelf  # type: ignore[attr-defined]

try:  # pragma: no cover - guard optional dependency in tests
    import argon2  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    argon2_stub = types.ModuleType("argon2")

    class _PasswordHasher:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - placeholder init
            return None

        def hash(self, password: str) -> str:  # noqa: D401 - placeholder behavior
            return f"hashed:{password}"

        def verify(self, hashed: str, password: str) -> bool:
            return hashed == f"hashed:{password}"

    argon2_stub.PasswordHasher = _PasswordHasher  # type: ignore[attr-defined]
    sys.modules["argon2"] = argon2_stub

    argon2_exceptions = types.ModuleType("argon2.exceptions")

    class _VerifyMismatchError(Exception):
        pass

    argon2_exceptions.VerifyMismatchError = _VerifyMismatchError  # type: ignore[attr-defined]
    sys.modules["argon2.exceptions"] = argon2_exceptions

try:  # pragma: no cover - guard optional dependency in tests
    import cryptography  # type: ignore  # noqa: F401 - imported for side effect
    from cryptography import fernet as _fernet  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    cryptography_stub = types.ModuleType("cryptography")
    fernet_stub = types.ModuleType("cryptography.fernet")

    class _Fernet:
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        def encrypt(self, data: bytes) -> bytes:
            return data

        def decrypt(self, token: bytes) -> bytes:
            return token

        @staticmethod
        def generate_key() -> bytes:
            return b"stub-key"

    fernet_stub.Fernet = _Fernet  # type: ignore[attr-defined]
    cryptography_stub.fernet = fernet_stub  # type: ignore[attr-defined]
    sys.modules["cryptography"] = cryptography_stub
    sys.modules["cryptography.fernet"] = fernet_stub

try:  # pragma: no cover - guard optional dependency in tests
    import requests  # type: ignore  # noqa: F401 - imported for side effect
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal envs
    requests_stub = types.ModuleType("requests")

    class _RequestException(Exception):
        pass

    class _HTTPError(_RequestException):
        pass

    def _stub_request(*_args, **_kwargs):
        raise RuntimeError("requests stub executed")

    requests_stub.post = _stub_request  # type: ignore[attr-defined]
    requests_stub.get = _stub_request  # type: ignore[attr-defined]
    requests_stub.exceptions = types.SimpleNamespace(  # type: ignore[attr-defined]
        RequestException=_RequestException,
        HTTPError=_HTTPError,
    )
    sys.modules["requests"] = requests_stub

import devsynth.fallback as fallback_module
from devsynth.adapters.provider_system import BaseProvider
from devsynth.metrics import reset_metrics


@pytest.fixture(autouse=True)
def _lmstudio_stub(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Provide a patched ``lmstudio`` module and opt into LM Studio resource tests.

    Tests under ``tests/unit/adapters`` rely on LM Studio provider behavior but
    should not import the real optional dependency or require the actual
    service.  This autouse fixture injects a lightweight module stub into
    ``sys.modules`` and sets the resource flag so provider code paths execute
    without hitting the network.
    """

    module = types.ModuleType("lmstudio")
    module.llm = MagicMock(name="lmstudio.llm")
    module.embedding_model = MagicMock(name="lmstudio.embedding_model")
    module.sync_api = types.SimpleNamespace(
        configure_default_client=MagicMock(
            name="lmstudio.sync_api.configure_default_client"
        ),
        list_downloaded_models=MagicMock(
            name="lmstudio.sync_api.list_downloaded_models"
        ),
    )

    monkeypatch.setitem(sys.modules, "lmstudio", module)
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "1")
    return module


@pytest_asyncio.fixture
async def async_retry_harness(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide a deterministic harness for exercising ``BaseProvider`` retries.

    The harness replaces the randomness inside ``retry_with_exponential_backoff``
    with a predictable sequence, records the jitter samples applied to backoff
    delays, and short-circuits ``time.sleep`` so async tests can await retry
    behavior without blocking.
    """

    reset_metrics()

    jitter_samples: list[float] = []
    jitter_values = deque([0.25, 0.75, 0.125, 0.875])

    def _deterministic_random() -> float:
        try:
            value = jitter_values.popleft()
        except IndexError:
            value = 0.5
        jitter_samples.append(value)
        return value

    monkeypatch.setattr(fallback_module.random, "random", _deterministic_random)

    sleep_calls: list[float] = []

    def _record_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(fallback_module.time, "sleep", _record_sleep)

    retry_config = {
        "max_retries": 3,
        "initial_delay": 0.1,
        "exponential_base": 2.0,
        "max_delay": 1.0,
        "jitter": True,
        "track_metrics": True,
        "conditions": [],
    }

    provider = BaseProvider(retry_config=retry_config)
    telemetry_events: list[SimpleNamespace] = []

    original_emit = provider._emit_retry_telemetry

    def _record_telemetry(
        self: BaseProvider, exc: Exception, attempt: int, delay: float
    ) -> None:
        telemetry_events.append(
            SimpleNamespace(exception=exc, attempt=attempt, delay=delay)
        )
        original_emit(exc, attempt, delay)

    provider._emit_retry_telemetry = MethodType(_record_telemetry, provider)

    async def invoke(
        *,
        fail_times: int,
        exception_factory: Callable[[int], Exception] | None = None,
    ) -> SimpleNamespace:
        attempts = 0

        def _exception(attempt: int) -> Exception:
            if exception_factory is not None:
                return exception_factory(attempt)
            return RuntimeError(f"retry-{attempt}")

        @provider.get_retry_decorator(retryable_exceptions=(RuntimeError,))
        def _unstable_call() -> str:
            nonlocal attempts
            attempts += 1
            if attempts <= fail_times:
                raise _exception(attempts)
            return f"ok-{attempts}"

        result = await asyncio.to_thread(_unstable_call)
        return SimpleNamespace(result=result, attempts=attempts)

    return SimpleNamespace(
        provider=provider,
        telemetry=telemetry_events,
        sleeps=sleep_calls,
        jitter=jitter_samples,
        invoke=invoke,
        retry_config=retry_config,
    )
