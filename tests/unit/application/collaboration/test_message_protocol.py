import json
import os
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest

if "argon2" not in sys.modules:
    argon2_stub = types.ModuleType("argon2")
    exceptions_stub = types.ModuleType("argon2.exceptions")

    class _VerifyMismatchError(Exception):
        """Placeholder mismatch error."""

    exceptions_stub.VerifyMismatchError = _VerifyMismatchError
    sys.modules["argon2.exceptions"] = exceptions_stub

    class _PasswordHasher:  # pragma: no cover - test shim
        def __init__(
            self, *args: object, **kwargs: object
        ) -> None:  # noqa: D401 - minimal stub
            """Stub password hasher for tests without argon2 dependency."""

        def hash(self, password: str) -> str:
            return password

        def verify(self, hashed: str, password: str) -> bool:
            return hashed == password

    argon2_stub.PasswordHasher = _PasswordHasher
    argon2_stub.exceptions = exceptions_stub
    sys.modules["argon2"] = argon2_stub


if "jsonschema" not in sys.modules:
    jsonschema_stub = types.ModuleType("jsonschema")

    def _validate(
        instance: object, schema: object, *args: object, **kwargs: object
    ) -> bool:
        return True

    class _DraftValidator:  # pragma: no cover - shim
        def __init__(
            self, *args: object, **kwargs: object
        ) -> None:  # noqa: D401 - stub
            """Minimal validator stub."""

        def validate(self, instance: object, schema: object) -> bool:
            return True

    jsonschema_stub.validate = _validate
    jsonschema_stub.Draft7Validator = _DraftValidator
    sys.modules["jsonschema"] = jsonschema_stub


if "toml" not in sys.modules:
    toml_stub = types.ModuleType("toml")

    def _loads(content: str, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    def _load(fp: object, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    class _TomlDecodeError(Exception):
        """Placeholder TOML decode error."""

    toml_stub.loads = _loads
    toml_stub.load = _load
    toml_stub.TomlDecodeError = _TomlDecodeError
    sys.modules["toml"] = toml_stub


if "yaml" not in sys.modules:
    yaml_stub = types.ModuleType("yaml")

    def _safe_load(stream: object) -> dict[str, object]:
        return {}

    yaml_stub.safe_load = _safe_load
    sys.modules["yaml"] = yaml_stub


if "pydantic" not in sys.modules:
    pydantic_stub = types.ModuleType("pydantic")

    class _BaseModel:  # pragma: no cover - shim
        def __init__(
            self, *args: object, **kwargs: object
        ) -> None:  # noqa: D401 - stub
            """Minimal pydantic-like base model."""

            if args:
                raise TypeError("Positional arguments are not supported in stub")
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _ValidationError(Exception):
        """Placeholder validation error."""

    pydantic_stub.BaseModel = _BaseModel
    pydantic_stub.ValidationError = _ValidationError
    pydantic_stub.Field = lambda default=None, **kwargs: default  # type: ignore[assignment]

    class _FieldValidationInfo:  # pragma: no cover - shim
        """Placeholder field validation info."""

    pydantic_stub.FieldValidationInfo = _FieldValidationInfo

    def _field_validator(*fields: str, **kwargs: object):  # pragma: no cover - shim
        def decorator(func):
            return func

        return decorator

    pydantic_stub.field_validator = _field_validator
    dataclasses_stub = types.ModuleType("pydantic.dataclasses")

    def _dataclass(
        cls: type | None = None, **kwargs: object
    ):  # pragma: no cover - shim
        def decorator(target: type) -> type:
            return target

        if cls is None:
            return decorator
        return cls

    dataclasses_stub.dataclass = _dataclass
    sys.modules["pydantic.dataclasses"] = dataclasses_stub
    pydantic_stub.dataclasses = dataclasses_stub
    sys.modules["pydantic"] = pydantic_stub


if "pydantic_settings" not in sys.modules:
    settings_stub = types.ModuleType("pydantic_settings")

    class _BaseSettings:  # pragma: no cover - shim
        model_config: dict[str, object] = {}

        def __init__(
            self, *args: object, **kwargs: object
        ) -> None:  # noqa: D401 - stub
            """Minimal settings base class."""

    class _SettingsConfigDict(dict):
        """Dictionary subclass placeholder."""

    settings_stub.BaseSettings = _BaseSettings
    settings_stub.SettingsConfigDict = _SettingsConfigDict
    sys.modules["pydantic_settings"] = settings_stub


if "devsynth.application.memory.memory_manager" not in sys.modules:
    memory_manager_stub = types.ModuleType("devsynth.application.memory.memory_manager")

    class _MemoryManager:  # pragma: no cover - shim
        def __init__(
            self, *args: object, **kwargs: object
        ) -> None:  # noqa: D401 - stub
            self.adapters: dict[str, object] = {}

        def update_item(self, *args: object, **kwargs: object) -> None:
            return None

        def flush_updates(self) -> None:
            return None

    memory_manager_stub.MemoryManager = _MemoryManager
    sys.modules["devsynth.application.memory.memory_manager"] = memory_manager_stub
    application_memory_stub = types.ModuleType("devsynth.application.memory")
    application_memory_stub.__path__ = []  # type: ignore[attr-defined]
    application_memory_stub.MemoryManager = _MemoryManager
    sys.modules["devsynth.application.memory"] = application_memory_stub


if "devsynth.config.settings" not in sys.modules:
    config_settings_stub = types.ModuleType("devsynth.config.settings")

    def _ensure_path_exists(path: object) -> None:  # pragma: no cover - shim
        return None

    def _get_settings() -> types.SimpleNamespace:
        return types.SimpleNamespace(wsde_settings={}, memory_store_type="memory")

    config_settings_stub.ensure_path_exists = _ensure_path_exists
    config_settings_stub.get_settings = _get_settings
    sys.modules["devsynth.config.settings"] = config_settings_stub


if "devsynth.config" not in sys.modules:
    config_stub = types.ModuleType("devsynth.config")
    config_stub.get_settings = lambda: types.SimpleNamespace(
        wsde_settings={}, memory_store_type="memory"
    )
    config_stub.get_llm_settings = lambda: {}
    config_stub.load_dotenv = lambda *args, **kwargs: None
    config_stub._settings = types.SimpleNamespace(
        wsde_settings={}, memory_store_type="memory"
    )
    sys.modules["devsynth.config"] = config_stub


from devsynth.application.collaboration.dto import (
    AgentPayload,
    MemorySyncPort,
    MessageFilter,
    TaskDescriptor,
    ensure_collaboration_payload,
    ensure_message_filter,
)
from devsynth.application.collaboration.message_protocol import (
    Message,
    MessageProtocol,
    MessageStore,
    MessageType,
)


@pytest.mark.medium
def test_send_message_priority_succeeds(tmp_path: Path) -> None:
    """High priority metadata remains prioritized after DTO conversion."""

    storage = tmp_path / "messages.json"
    proto = MessageProtocol(store=MessageStore(storage_file=str(storage)))

    proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="s",
        content="c",
        metadata={"priority": "high", "channel": "inbox"},
    )
    proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="s2",
        content="c2",
    )

    assert proto.history[0].metadata is not None
    assert isinstance(proto.history[0].metadata, MemorySyncPort)
    assert proto.history[0].metadata.priority == "high"
    assert proto.history[0].metadata.channel == "inbox"


@pytest.mark.medium
def test_get_messages_filtered_succeeds(tmp_path: Path) -> None:
    """Messages retrieved via filters preserve DTO content."""

    storage = tmp_path / "messages.json"
    proto = MessageProtocol(store=MessageStore(storage_file=str(storage)))
    payload = TaskDescriptor(task_id="task-1", summary="demo", tags=("alpha", "beta"))
    msg = proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.DECISION_REQUEST,
        subject="x",
        content=payload,
    )

    filter_spec = MessageFilter(message_type=MessageType.DECISION_REQUEST.value)
    result = proto.get_messages("b", filter_spec)

    assert result == [msg]
    assert isinstance(result[0].content, TaskDescriptor)
    assert result[0].content == payload


@pytest.mark.medium
def test_dto_round_trip_and_deterministic_serialization(tmp_path: Path) -> None:
    """DTO helpers yield deterministic dictionaries suitable for persistence."""

    os.environ["DEVSYNTH_NO_FILE_LOGGING"] = "0"
    storage = tmp_path / "messages.json"
    store = MessageStore(storage_file=str(storage))
    proto = MessageProtocol(store=store)

    payload = AgentPayload(
        agent_id="agent-123",
        display_name="Analyst",
        role="reviewer",
        attributes={"b": 2, "a": 1},
        payload=["checkpoint", "complete"],
    )
    metadata = MemorySyncPort(
        adapter="tinydb",
        channel="primary",
        priority="medium",
        options={"retention": "long"},
    )

    proto.send_message(
        sender="analyst",
        recipients=["lead"],
        message_type=MessageType.STATUS_UPDATE,
        subject="Report",
        content=payload,
        metadata=metadata,
    )

    serialized_payload = payload.to_dict()
    assert list(serialized_payload.keys()) == [
        "dto_type",
        "agent_id",
        "display_name",
        "role",
        "status",
        "summary",
        "attributes",
        "payload",
    ]
    assert list(serialized_payload["attributes"].keys()) == ["a", "b"]
    assert AgentPayload.from_dict(serialized_payload) == payload

    reloaded_store = MessageStore(storage_file=str(storage))
    reloaded_messages = reloaded_store.get_messages()
    assert len(reloaded_messages) == 1
    reloaded = reloaded_messages[0]
    assert isinstance(reloaded.content, AgentPayload)
    assert reloaded.content == payload
    assert reloaded.metadata == metadata

    with storage.open("r", encoding="utf-8") as handle:
        file_data = json.load(handle)
    assert file_data["messages"][0]["content"]["attributes"] == {"a": 1, "b": 2}


@pytest.mark.medium
def test_get_messages_accepts_enum_mapping(tmp_path: Path) -> None:
    """Enum-based filter mappings are normalized via ensure_message_filter."""

    storage = tmp_path / "enum-filter.json"
    proto = MessageProtocol(store=MessageStore(storage_file=str(storage)))
    message = proto.send_message(
        sender="alpha",
        recipients=["beta"],
        message_type=MessageType.STATUS_UPDATE,
        subject="Status",
        content={"payload": "ok"},
    )

    results = proto.get_messages(filters={"message_type": MessageType.STATUS_UPDATE})

    assert results == [message]


@pytest.mark.medium
def test_message_store_filters_by_time_and_subject(tmp_path: Path) -> None:
    """MessageStore applies temporal and subject filters consistently."""

    storage = tmp_path / "filtered.json"
    store = MessageStore(storage_file=str(storage))
    earlier = datetime.now() - timedelta(hours=1)
    later = datetime.now()
    base_payload = AgentPayload(summary="payload")

    first = Message(
        message_id="first",
        message_type=MessageType.NOTIFICATION,
        sender="alpha",
        recipients=["beta"],
        subject="Alpha update",
        content=base_payload,
        metadata=None,
        timestamp=earlier,
    )
    second = Message(
        message_id="second",
        message_type=MessageType.NOTIFICATION,
        sender="alpha",
        recipients=["beta"],
        subject="Beta Update",
        content=base_payload,
        metadata=None,
        timestamp=later,
    )
    store.add_message(first)
    store.add_message(second)

    filtered = store.get_messages(
        MessageFilter(since=earlier + timedelta(minutes=30), subject_contains="beta")
    )

    assert [message.subject for message in filtered] == ["Beta Update"]

    with pytest.raises(ValueError):
        store.get_messages(MessageFilter(message_type="unknown"))


@pytest.mark.fast
def test_ensure_collaboration_payload_protocol_support() -> None:
    """Objects implementing the AgentPayloadLike protocol are supported."""

    class CustomAgentPayload:
        def to_agent_payload(self) -> AgentPayload:
            return AgentPayload(summary="custom")

    payload = ensure_collaboration_payload(CustomAgentPayload())

    assert isinstance(payload, AgentPayload)
    assert payload.summary == "custom"

    with pytest.raises(TypeError):
        ensure_collaboration_payload(object())  # type: ignore[arg-type]


@pytest.mark.fast
def test_ensure_message_filter_rejects_invalid_input() -> None:
    """ensure_message_filter rejects unexpected input types."""

    base_filter = MessageFilter(message_type=MessageType.NOTIFICATION.value)
    assert ensure_message_filter(base_filter) is base_filter

    with pytest.raises(TypeError):
        ensure_message_filter(42)  # type: ignore[arg-type]


@pytest.mark.fast
def test_message_filter_invalid_timestamp_raises() -> None:
    """Constructing a MessageFilter with invalid timestamps fails early."""

    with pytest.raises(ValueError):
        MessageFilter(since="not-a-timestamp")
