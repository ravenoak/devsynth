"""S3-backed memory adapter."""

from __future__ import annotations

import importlib
import json
import uuid
from collections.abc import Mapping
from typing import Any, Protocol, TypedDict, cast

from ....domain.models.memory import MemoryItem, MemoryType, SerializedMemoryItem
from ....exceptions import MemoryTransactionError
from ....logging_setup import DevSynthLogger
from ..dto import (
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    build_memory_record,
    build_query_results,
)
from ..metadata_serialization import from_serializable, to_serializable
from .storage_adapter import StorageAdapter

_BOTO3_ERROR: ModuleNotFoundError | None = None
try:  # pragma: no cover - optional dependency
    _boto3 = importlib.import_module("boto3")
    _exceptions = importlib.import_module("botocore.exceptions")
    _ImportedClientError = getattr(_exceptions, "ClientError")
except ModuleNotFoundError as exc:  # pragma: no cover - missing optional dependency
    _boto3 = cast(Any, None)

    class _FallbackClientError(Exception):
        """Fallback client error when botocore isn't installed."""

    _BOTO3_ERROR = exc
    _ImportedClientError = _FallbackClientError

boto3 = _boto3
ClientError = _ImportedClientError

logger = DevSynthLogger(__name__)


class S3ObjectBody(Protocol):
    """Minimal protocol for the streaming body returned by boto3."""

    def read(self) -> bytes: ...


class S3GetObjectResponse(TypedDict, total=False):
    Body: S3ObjectBody


class S3ListEntry(TypedDict, total=False):
    Key: str


class S3ListResponse(TypedDict, total=False):
    Contents: list[S3ListEntry]


class S3ClientProtocol(Protocol):
    """Subset of the boto3 S3 client used by :class:`S3MemoryAdapter`."""

    def put_object(self, *, Bucket: str, Key: str, Body: str) -> object: ...

    def get_object(self, *, Bucket: str, Key: str) -> S3GetObjectResponse: ...

    def list_objects_v2(self, *, Bucket: str) -> S3ListResponse: ...

    def delete_object(self, *, Bucket: str, Key: str) -> object: ...


class S3MemoryAdapter(StorageAdapter):
    """Store memory items in an S3 bucket."""

    backend_type = "s3"

    def __init__(self, bucket: str, client: S3ClientProtocol | None = None):
        if boto3 is None:  # pragma: no cover - defensive
            raise ImportError("boto3 is required for S3MemoryAdapter") from _BOTO3_ERROR
        self.bucket = bucket
        raw_client = client or boto3.client("s3")
        self.client = cast(S3ClientProtocol, raw_client)

    # ------------------------------------------------------------------
    # Core storage operations
    # ------------------------------------------------------------------
    def store(self, item: MemoryItem, transaction_id: str | None = None) -> str:
        if transaction_id is not None:
            raise MemoryTransactionError(
                "Transactions are not supported for S3MemoryAdapter",
                transaction_id=transaction_id,
                store_type=self.backend_type,
                operation="store",
            )
        if not item.id:
            item.id = str(uuid.uuid4())
        metadata_payload = cast(MemoryMetadata | None, item.metadata)
        payload: SerializedMemoryItem = {
            "id": item.id,
            "content": item.content,
            "memory_type": item.memory_type.value,
            "metadata": cast(MemoryMetadata, to_serializable(metadata_payload)),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        data = json.dumps(payload)
        self.client.put_object(Bucket=self.bucket, Key=item.id, Body=data)
        return str(item.id)

    def retrieve(self, item_id: str) -> MemoryRecord | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=item_id)
        except ClientError:
            return None
        body = obj.get("Body")
        if body is None:
            return None
        raw = cast(SerializedMemoryItem, json.loads(body.read()))
        metadata_payload = raw.get("metadata")
        metadata: MemoryMetadata | None = None
        if isinstance(metadata_payload, Mapping):
            metadata = from_serializable(metadata_payload)
        item = MemoryItem(
            id=raw["id"],
            content=raw["content"],
            memory_type=MemoryType.from_raw(raw["memory_type"]),
            metadata=metadata,
        )
        return build_memory_record(item, source=self.backend_type)

    def search(self, query: Mapping[str, str | MemoryType]) -> list[MemoryRecord]:
        items: list[MemoryRecord] = []
        resp = self.client.list_objects_v2(Bucket=self.bucket)
        for obj in resp.get("Contents", []):
            item = self.retrieve(obj["Key"])
            if not item:
                continue
            match = True
            metadata = item.metadata or {}
            for key, value in query.items():
                if key == "type":
                    expected = MemoryType.from_raw(value)
                    if item.memory_type != expected:
                        match = False
                        break
                elif metadata.get(key) != value:
                    match = False
                    break
            if match:
                items.append(item)
        return items

    def delete(self, item_id: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=item_id)
            return True
        except ClientError:  # pragma: no cover - defensive
            return False

    # ------------------------------------------------------------------
    # Transaction API (unsupported)
    # ------------------------------------------------------------------
    def begin_transaction(
        self, transaction_id: str | None = None
    ) -> str:  # pragma: no cover - simple
        raise MemoryTransactionError(
            "Transactions are not supported", store_type=self.backend_type
        )

    def commit_transaction(
        self, transaction_id: str | None = None
    ) -> bool:  # pragma: no cover - simple
        raise MemoryTransactionError(
            "Transactions are not supported",
            transaction_id=transaction_id,
            store_type=self.backend_type,
        )

    def rollback_transaction(
        self, transaction_id: str | None = None
    ) -> bool:  # pragma: no cover - simple
        raise MemoryTransactionError(
            "Transactions are not supported",
            transaction_id=transaction_id,
            store_type=self.backend_type,
        )

    def is_transaction_active(
        self, transaction_id: str
    ) -> bool:  # pragma: no cover - simple
        return False
