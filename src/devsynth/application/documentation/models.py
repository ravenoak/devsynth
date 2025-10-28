"""Typed models for documentation ingestion and fetching."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

MetadataScalar = str | int | float | bool | None
"""Primitive metadata value supported by documentation manifests."""

Metadata = dict[str, MetadataScalar]
"""Standard metadata mapping used throughout documentation workflows."""


@dataclass(slots=True)
class DocumentationManifest:
    """Structured representation of ingested documentation."""

    content: str
    metadata: Metadata = field(default_factory=dict)
    identifier: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialise the manifest into a dictionary suitable for legacy APIs."""
        payload: dict[str, object] = {
            "content": self.content,
            "metadata": dict(self.metadata),
        }
        if self.identifier is not None:
            payload["id"] = self.identifier
        return payload

    def with_identifier(self, identifier: str) -> DocumentationManifest:
        """Return a new manifest with the provided identifier."""
        return DocumentationManifest(
            content=self.content,
            metadata=dict(self.metadata),
            identifier=identifier,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> DocumentationManifest:
        """Construct a manifest from a mapping."""
        content = str(payload.get("content", ""))
        metadata = _coerce_metadata(payload.get("metadata", {}))
        identifier = payload.get("id")
        return cls(
            content=content,
            metadata=metadata,
            identifier=str(identifier) if isinstance(identifier, str) else None,
        )


@dataclass(slots=True)
class DocumentationChunk:
    """A single documentation chunk produced by fetchers."""

    title: str
    content: str
    metadata: Metadata = field(default_factory=dict)

    def to_json(self) -> dict[str, object]:
        """Serialise the chunk for JSON caching."""
        return {
            "title": self.title,
            "content": self.content,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, object]) -> DocumentationChunk:
        """Create a chunk from cached JSON data."""
        title = str(payload.get("title", ""))
        content = str(payload.get("content", ""))
        metadata = _coerce_metadata(payload.get("metadata", {}))
        return cls(title=title, content=content, metadata=metadata)


@dataclass(slots=True)
class DownloadManifest:
    """Result of a network download attempt."""

    url: str
    success: bool
    status_code: int | None = None
    content: str = ""
    error: str | None = None

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return self.success


def _coerce_metadata(raw: object) -> Metadata:
    """Coerce a mapping-like object into :class:`Metadata`."""
    metadata: Metadata = {}
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                metadata[str(key)] = value
            else:
                metadata[str(key)] = str(value)
    return metadata
