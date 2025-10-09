"""Unit tests for collaboration application components."""

import sys
from dataclasses import dataclass as _dataclass
from types import ModuleType


def _ensure_stub_module(name: str, module: ModuleType) -> None:
    sys.modules.setdefault(name, module)


if "yaml" not in sys.modules:
    yaml_stub = ModuleType("yaml")
    yaml_stub.safe_load = lambda *args, **kwargs: {}
    yaml_stub.safe_dump = lambda *args, **kwargs: None
    _ensure_stub_module("yaml", yaml_stub)

if "jsonschema" not in sys.modules:
    jsonschema_stub = ModuleType("jsonschema")
    jsonschema_stub.validate = lambda *args, **kwargs: None

    class _ValidationError(Exception):
        pass

    exceptions_stub = ModuleType("jsonschema.exceptions")
    exceptions_stub.ValidationError = _ValidationError
    exceptions_stub.SchemaError = _ValidationError
    jsonschema_stub.exceptions = exceptions_stub
    _ensure_stub_module("jsonschema", jsonschema_stub)
    _ensure_stub_module("jsonschema.exceptions", exceptions_stub)

if "toml" not in sys.modules:
    toml_stub = ModuleType("toml")
    toml_stub.load = lambda *args, **kwargs: {}
    toml_stub.dump = lambda *args, **kwargs: None
    _ensure_stub_module("toml", toml_stub)

if "pydantic" not in sys.modules:
    pydantic_stub = ModuleType("pydantic")

    class _PydanticValidationError(Exception):
        pass

    def _field(*_args, default=None, **_kwargs):
        return default

    def _field_validator(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

    pydantic_stub.ValidationError = _PydanticValidationError
    pydantic_stub.Field = _field
    pydantic_stub.field_validator = _field_validator

    class _FieldValidationInfo:  # pragma: no cover - stub
        pass

    pydantic_stub.FieldValidationInfo = _FieldValidationInfo
    dataclasses_stub = ModuleType("pydantic.dataclasses")
    dataclasses_stub.dataclass = _dataclass
    pydantic_stub.dataclasses = dataclasses_stub
    _ensure_stub_module("pydantic", pydantic_stub)
    _ensure_stub_module("pydantic.dataclasses", dataclasses_stub)

if "pydantic_settings" not in sys.modules:
    settings_stub = ModuleType("pydantic_settings")
    settings_stub.BaseSettings = object
    settings_stub.SettingsConfigDict = dict
    _ensure_stub_module("pydantic_settings", settings_stub)

if "argon2" not in sys.modules:
    argon2_stub = ModuleType("argon2")

    class _StubPasswordHasher:
        def __init__(self, *_args, **_kwargs):
            pass

        def hash(self, value):
            return f"hash:{value}"

        def verify(self, _hashed, _value):
            return True

        def check_needs_rehash(self, _hashed):
            return False

    exceptions_module = ModuleType("argon2.exceptions")
    exceptions_module.VerifyMismatchError = RuntimeError
    argon2_stub.PasswordHasher = _StubPasswordHasher
    argon2_stub.exceptions = exceptions_module
    _ensure_stub_module("argon2", argon2_stub)
    _ensure_stub_module("argon2.exceptions", exceptions_module)
