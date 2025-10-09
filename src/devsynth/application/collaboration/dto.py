"""Typed data-transfer objects for collaboration workflows."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from dataclasses import MISSING, dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    Union,
    ValuesView,
    cast,
    get_args,
    get_origin,
    runtime_checkable,
)

__all__ = [
    "AgentPayload",
    "TaskDescriptor",
    "AgentPayloadLike",
    "TaskDescriptorLike",
    "MessageFilter",
    "MessageFilterLike",
    "MessageFilterInput",
    "ConsensusOutcome",
    "AgentOpinionRecord",
    "ConflictRecord",
    "SynthesisArtifact",
    "ReviewDecision",
    "PeerReviewRecord",
    "MemorySyncPort",
    "CollaborationDTO",
    "MessagePayload",
    "deserialize_collaboration_dto",
    "serialize_collaboration_dto",
    "serialize_message_payload",
    "deserialize_message_payload",
    "ensure_collaboration_payload",
    "ensure_message_filter",
    "ensure_memory_sync_port",
    "serialize_memory_sync_port",
]


T = TypeVar("T", bound="BaseDTO")

JSONPrimitive: TypeAlias = Union[str, int, float, bool, None]
JSONValue: TypeAlias = Union[
    JSONPrimitive,
    Sequence["JSONValue"],
    Mapping[str, "JSONValue"],
]
JSONMapping: TypeAlias = Mapping[str, JSONValue]


@runtime_checkable
class AgentPayloadLike(Protocol):
    """Protocol for objects that can convert themselves into :class:`AgentPayload`."""

    def to_agent_payload(self) -> "AgentPayload":
        """Return an :class:`AgentPayload` instance."""


@runtime_checkable
class TaskDescriptorLike(Protocol):
    """Protocol for objects convertible into :class:`TaskDescriptor`."""

    def to_task_descriptor(self) -> "TaskDescriptor":
        """Return a :class:`TaskDescriptor` instance."""


@runtime_checkable
class MessageFilterLike(Protocol):
    """Protocol for objects convertible into :class:`MessageFilter`."""

    def to_message_filter(self) -> "MessageFilter":
        """Return a :class:`MessageFilter` instance."""


def _ordered_mapping(items: Iterable[Tuple[str, JSONValue]]) -> Dict[str, JSONValue]:
    return dict(OrderedDict(sorted(items, key=lambda item: item[0])))


def _serialize_value(value: Any) -> JSONValue:
    if isinstance(value, BaseDTO):
        return value.to_dict()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, MappingABC):
        return _ordered_mapping((str(k), _serialize_value(v)) for k, v in value.items())
    if isinstance(value, SequenceABC) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [_serialize_value(v) for v in value]
    return cast(JSONValue, value)


def _normalize_mapping(value: MappingABC[str, Any]) -> Dict[str, JSONValue]:
    return _ordered_mapping(
        (str(k), _deserialize_arbitrary(v)) for k, v in value.items()
    )


def _deserialize_arbitrary(value: Any) -> JSONValue:
    if isinstance(value, MappingABC):
        return _normalize_mapping(value)
    if isinstance(value, SequenceABC) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [_deserialize_arbitrary(v) for v in value]
    return cast(JSONValue, value)


def _is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        return any(arg is type(None) for arg in args)
    return False


def _unwrap_optional(annotation: Any) -> Any:
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    return args[0] if args else Any


def _coerce_value(annotation: Any, value: Any) -> Any:
    if value is None:
        return None

    origin = get_origin(annotation)

    if origin is Union and _is_optional(annotation):
        return _coerce_value(_unwrap_optional(annotation), value)

    if isinstance(value, BaseDTO):
        return value

    if isinstance(annotation, type) and issubclass_safe(annotation, BaseDTO):
        dto_cls = cast(Type[BaseDTO], annotation)
        mapping_value = cast(Mapping[str, Any], value)
        return dto_cls.from_dict(mapping_value)

    if origin in {list, tuple}:
        item_type = get_args(annotation)[0] if get_args(annotation) else Any
        coerced = [_coerce_value(item_type, v) for v in value]
        return tuple(coerced) if origin is tuple else coerced

    if origin in {dict, Mapping} and isinstance(value, MappingABC):
        return _normalize_mapping(value)

    return _deserialize_arbitrary(value)


def issubclass_safe(candidate: Any, parent: Type[Any]) -> bool:
    try:
        return isinstance(candidate, type) and issubclass(candidate, parent)
    except TypeError:
        return False


class BaseDTO:
    """Base helpers for DTO serialization."""

    dto_type: ClassVar[str]
    extra_field_name: ClassVar[Optional[str]] = None

    def to_dict(self) -> Dict[str, JSONValue]:
        result_items: List[Tuple[str, JSONValue]] = [("dto_type", self.dto_type)]
        dataclass_type = cast(Type[Any], type(self))
        for field_info in fields(dataclass_type):
            value = getattr(self, field_info.name)
            result_items.append((field_info.name, _serialize_value(value)))
        return dict(OrderedDict(result_items))

    # Mapping-style helpers to ease migration for legacy consumers
    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def items(self) -> ItemsView[str, Any]:
        return self.to_dict().items()

    def keys(self) -> KeysView[str]:
        return self.to_dict().keys()

    def values(self) -> ValuesView[Any]:
        return self.to_dict().values()

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, Any]) -> T:
        if not isinstance(data, MappingABC):
            raise TypeError(
                f"Expected mapping for {cls.__name__}, received {type(data)!r}"
            )

        prepared: Dict[str, Any] = {}
        for key, value in data.items():
            if key == "dto_type":
                continue
            prepared[str(key)] = value

        dataclass_type = cast(Type[Any], cls)
        field_map = {f.name: f for f in fields(dataclass_type)}
        kwargs: Dict[str, Any] = {}
        extras: Dict[str, Any] = {}

        for name, value in prepared.items():
            field_info = field_map.get(name)
            if field_info is None:
                extras[name] = _deserialize_arbitrary(value)
                continue
            kwargs[name] = _coerce_value(field_info.type, value)

        extra_field = cls.extra_field_name
        if extras:
            if extra_field and extra_field in field_map:
                current = kwargs.get(extra_field)
                if current is None:
                    current_map: Dict[str, Any] = {}
                elif isinstance(current, MappingABC):
                    current_map = dict(current)
                else:
                    current_map = {}
                current_map.update(extras)
                kwargs[extra_field] = _normalize_mapping(current_map)
            else:
                raise ValueError(
                    f"Unexpected extra fields for {cls.__name__}: {sorted(extras.keys())}"
                )

        for field_info in field_map.values():
            if field_info.init and field_info.name not in kwargs:
                if field_info.default is not MISSING:
                    kwargs[field_info.name] = field_info.default
                else:
                    default_factory = getattr(field_info, "default_factory", MISSING)
                    if default_factory is not MISSING:
                        factory = cast(Callable[[], Any], default_factory)
                        kwargs[field_info.name] = factory()

        return cls(**kwargs)


def _dto_type_name(cls: Type[BaseDTO]) -> str:
    return getattr(cls, "dto_type", cls.__name__)


def _register_dto(cls: Type[T]) -> Type[T]:
    dto_registry[_dto_type_name(cls)] = cls
    return cls


@dataclass(frozen=True, slots=True)
class AgentPayload(BaseDTO):
    dto_type: ClassVar[str] = "AgentPayload"
    extra_field_name: ClassVar[str] = "attributes"

    agent_id: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
    attributes: JSONMapping = field(default_factory=dict)
    payload: Optional[JSONValue] = None


@dataclass(frozen=True, slots=True)
class TaskDescriptor(BaseDTO):
    dto_type: ClassVar[str] = "TaskDescriptor"
    extra_field_name: ClassVar[str] = "metadata"

    task_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    tags: Tuple[str, ...] = ()
    metadata: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConsensusOutcome(BaseDTO):
    dto_type: ClassVar[str] = "ConsensusOutcome"
    extra_field_name: ClassVar[str] = "metadata"

    consensus_id: Optional[str] = None
    task_id: Optional[str] = None
    method: Optional[str] = None
    achieved: Optional[bool] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    participants: Tuple[str, ...] = ()
    agent_opinions: Tuple["AgentOpinionRecord", ...] = ()
    conflicts: Tuple["ConflictRecord", ...] = ()
    conflicts_identified: int = 0
    synthesis: Optional["SynthesisArtifact"] = None
    majority_opinion: Optional[str] = None
    stakeholder_explanation: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: JSONMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized_metadata = (
            _normalize_mapping(self.metadata)
            if isinstance(self.metadata, MappingABC)
            else {}
        )
        object.__setattr__(self, "metadata", normalized_metadata)

        opinions = tuple(
            sorted(
                self.agent_opinions,
                key=lambda opinion: (opinion.agent_id or "", opinion.timestamp or ""),
            )
        )
        object.__setattr__(self, "agent_opinions", opinions)

        conflicts = tuple(
            sorted(
                self.conflicts,
                key=lambda conflict: (
                    conflict.conflict_id or "",
                    conflict.agent_a or "",
                ),
            )
        )
        object.__setattr__(self, "conflicts", conflicts)

        if not self.participants and opinions:
            participants = tuple(
                OrderedDict(
                    (record.agent_id, None) for record in opinions if record.agent_id
                )
            )
            object.__setattr__(self, "participants", participants)
        else:
            object.__setattr__(
                self,
                "participants",
                tuple(
                    OrderedDict(
                        (participant, None) for participant in self.participants
                    )
                ),
            )

        conflict_total = len(conflicts)
        if conflict_total and conflict_total != self.conflicts_identified:
            object.__setattr__(self, "conflicts_identified", conflict_total)

        if self.timestamp and hasattr(self.timestamp, "isoformat"):
            object.__setattr__(self, "timestamp", self.timestamp.isoformat())


@dataclass(frozen=True, slots=True)
class AgentOpinionRecord(BaseDTO):
    dto_type: ClassVar[str] = "AgentOpinionRecord"
    extra_field_name: ClassVar[str] = "metadata"

    agent_id: Optional[str] = None
    opinion: Optional[str] = None
    rationale: Optional[str] = None
    timestamp: Optional[str] = None
    weight: Optional[float] = None
    metadata: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConflictRecord(BaseDTO):
    dto_type: ClassVar[str] = "ConflictRecord"
    extra_field_name: ClassVar[str] = "metadata"

    conflict_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_a: Optional[str] = None
    agent_b: Optional[str] = None
    opinion_a: Optional[str] = None
    opinion_b: Optional[str] = None
    rationale_a: Optional[str] = None
    rationale_b: Optional[str] = None
    severity_label: Optional[str] = None
    severity_score: Optional[float] = None
    metadata: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SynthesisArtifact(BaseDTO):
    dto_type: ClassVar[str] = "SynthesisArtifact"
    extra_field_name: ClassVar[str] = "metadata"

    text: Optional[str] = None
    key_points: Tuple[str, ...] = ()
    expertise_weights: Mapping[str, float] = field(default_factory=dict)
    conflict_resolution_method: Optional[str] = None
    readability_score: Mapping[str, float] = field(default_factory=dict)
    metadata: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReviewDecision(BaseDTO):
    dto_type: ClassVar[str] = "ReviewDecision"
    extra_field_name: ClassVar[str] = "metadata"

    decision_id: Optional[str] = None
    reviewer: Optional[str] = None
    approved: Optional[bool] = None
    notes: Optional[str] = None
    score: Optional[float] = None
    metadata: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PeerReviewRecord(BaseDTO):
    dto_type: ClassVar[str] = "PeerReviewRecord"
    extra_field_name: ClassVar[str] = "metadata"

    task: Optional[TaskDescriptor] = None
    decision: Optional[ReviewDecision] = None
    consensus: Optional[ConsensusOutcome] = None
    reviewers: Tuple[str, ...] = ()
    notes: Optional[str] = None
    metadata: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemorySyncPort(BaseDTO):
    dto_type: ClassVar[str] = "MemorySyncPort"
    extra_field_name: ClassVar[str] = "options"

    adapter: str = "conversation"
    channel: str = "default"
    priority: Optional[str] = None
    options: JSONMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MessageFilter(BaseDTO):
    """Structured message filter specification."""

    dto_type: ClassVar[str] = "MessageFilter"

    message_type: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    subject_contains: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None

    def __post_init__(self) -> None:
        for field_name in ("since", "until"):
            value = getattr(self, field_name)
            if isinstance(value, str):
                try:
                    parsed = datetime.fromisoformat(value)
                except ValueError as exc:  # pragma: no cover - defensive
                    raise ValueError(
                        f"Invalid ISO timestamp for {field_name}: {value!r}"
                    ) from exc
                object.__setattr__(self, field_name, parsed)

    def with_sender(self, sender: Optional[str]) -> "MessageFilter":
        """Return a new filter with the provided sender."""

        if sender == self.sender:
            return self
        data = self.to_dict()
        data["sender"] = sender
        return MessageFilter.from_dict(data)


MessageFilterInput = Union[MessageFilter, MessageFilterLike, Mapping[str, JSONValue]]


dto_registry: Dict[str, Type[BaseDTO]] = {}

for cls in (
    AgentPayload,
    TaskDescriptor,
    AgentOpinionRecord,
    ConflictRecord,
    SynthesisArtifact,
    ConsensusOutcome,
    ReviewDecision,
    PeerReviewRecord,
    MemorySyncPort,
):
    _register_dto(cls)


CollaborationDTO = Union[
    AgentPayload,
    TaskDescriptor,
    ConsensusOutcome,
    ReviewDecision,
    PeerReviewRecord,
]

CollaborationPayloadInput = Union[
    CollaborationDTO,
    AgentPayloadLike,
    TaskDescriptorLike,
    JSONValue,
]

MessagePayload = Union[CollaborationDTO, JSONValue]


def serialize_collaboration_dto(dto: CollaborationDTO) -> Dict[str, JSONValue]:
    return dto.to_dict()


def deserialize_collaboration_dto(data: Mapping[str, Any]) -> CollaborationDTO:
    if not isinstance(data, MappingABC):
        raise TypeError("Collaborative payload must be provided as a mapping")

    dto_type = data.get("dto_type")
    if dto_type:
        dto_cls = dto_registry.get(str(dto_type))
        if dto_cls is None:
            raise ValueError(f"Unknown dto_type '{dto_type}'")
        instance = dto_cls.from_dict(data)
        if isinstance(instance, MemorySyncPort):
            raise TypeError("Expected collaboration DTO, received MemorySyncPort")
        return cast(CollaborationDTO, instance)

    # Fallback to AgentPayload to avoid data loss for legacy entries.
    return cast(CollaborationDTO, AgentPayload.from_dict(data))


def serialize_message_payload(payload: MessagePayload) -> JSONValue:
    if isinstance(payload, BaseDTO):
        return payload.to_dict()
    if isinstance(payload, MappingABC):
        return _normalize_mapping(payload)
    if isinstance(payload, SequenceABC) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        return [_serialize_value(item) for item in payload]
    return cast(JSONValue, payload)


def deserialize_message_payload(data: Any) -> MessagePayload:
    if isinstance(data, MappingABC):
        dto_type = data.get("dto_type")
        if dto_type:
            dto_cls = dto_registry.get(str(dto_type))
            if dto_cls is not None:
                instance = dto_cls.from_dict(data)
                if isinstance(instance, MemorySyncPort):
                    return instance.to_dict()
                return cast(MessagePayload, instance)
        return cast(MessagePayload, _normalize_mapping(data))
    if isinstance(data, SequenceABC) and not isinstance(data, (str, bytes, bytearray)):
        return cast(
            MessagePayload,
            [_deserialize_arbitrary(item) for item in data],
        )
    return cast(MessagePayload, data)


def ensure_collaboration_payload(
    content: CollaborationPayloadInput,
    *,
    default: Type[CollaborationDTO] = AgentPayload,
) -> CollaborationDTO:
    if isinstance(content, BaseDTO):
        if isinstance(content, MemorySyncPort):
            raise TypeError("MemorySyncPort cannot be used as message content")
        return content

    if isinstance(content, AgentPayloadLike):
        agent_candidate = content.to_agent_payload()
        return ensure_collaboration_payload(agent_candidate, default=default)

    if isinstance(content, TaskDescriptorLike):
        descriptor_candidate = content.to_task_descriptor()
        return ensure_collaboration_payload(descriptor_candidate, default=default)

    if isinstance(content, MappingABC):
        try:
            return deserialize_collaboration_dto(dict(content))
        except Exception:
            pass

    if isinstance(content, str):
        dto_default = cast(Type[BaseDTO], default)
        return cast(CollaborationDTO, dto_default.from_dict({"summary": content}))

    if isinstance(content, (int, float, bool)):
        dto_default = cast(Type[BaseDTO], default)
        return cast(
            CollaborationDTO,
            dto_default.from_dict({"payload": content}),
        )

    if isinstance(content, SequenceABC) and not isinstance(
        content, (str, bytes, bytearray)
    ):
        dto_default = cast(Type[BaseDTO], default)
        return cast(
            CollaborationDTO,
            dto_default.from_dict({"payload": list(content)}),
        )

    if content is None:
        dto_default = cast(Type[BaseDTO], default)
        return cast(CollaborationDTO, dto_default.from_dict({}))

    raise TypeError(
        f"Unsupported message content type for collaboration payload: {type(content)!r}"
    )


def ensure_memory_sync_port(
    metadata: Optional[Union[MemorySyncPort, Mapping[str, JSONValue]]],
) -> Optional[MemorySyncPort]:
    if metadata is None:
        return None
    if isinstance(metadata, MemorySyncPort):
        return metadata
    if isinstance(metadata, MappingABC):
        base = dict(metadata)
        adapter = str(base.pop("adapter", "conversation"))
        channel = str(base.pop("channel", "default"))
        priority_value = base.pop("priority", None)
        priority = str(priority_value) if priority_value is not None else None
        nested_options = base.pop("options", {})
        base.pop("dto_type", None)
        if isinstance(nested_options, MappingABC):
            for key, value in nested_options.items():
                base.setdefault(key, value)
        options = _normalize_mapping(base) if base else {}
        return MemorySyncPort(
            adapter=adapter, channel=channel, priority=priority, options=options
        )
    raise TypeError("Metadata must be MemorySyncPort or mapping type")


def serialize_memory_sync_port(
    metadata: Optional[MemorySyncPort],
) -> Optional[Dict[str, JSONValue]]:
    if metadata is None:
        return None
    return metadata.to_dict()


def ensure_message_filter(
    filters: Optional[MessageFilterInput],
) -> Optional[MessageFilter]:
    if filters is None:
        return None
    if isinstance(filters, MessageFilter):
        return filters
    if isinstance(filters, MessageFilterLike):
        return filters.to_message_filter()
    if isinstance(filters, MappingABC):
        try:
            base: Dict[str, Any] = dict(filters)
            mt_value: Any = base.get("message_type")
            if isinstance(mt_value, Enum):
                base["message_type"] = str(mt_value.value)
            elif mt_value is not None and not isinstance(mt_value, str):
                base["message_type"] = str(mt_value)
            return MessageFilter.from_dict(base)
        except Exception as exc:  # pragma: no cover - defensive
            raise TypeError("Invalid mapping for MessageFilter") from exc
    raise TypeError(f"Unsupported filter specification: {type(filters)!r}")
