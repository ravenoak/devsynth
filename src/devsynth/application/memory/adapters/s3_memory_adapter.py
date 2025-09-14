"""S3-backed memory adapter."""

from __future__ import annotations

import importlib
import json
import uuid
from collections.abc import Mapping
from typing import Any  # S3 client treated as dynamic ``Any``
from typing import Any as S3Client
from typing import cast

from ....domain.models.memory import MemoryItem, MemoryType
from ....exceptions import MemoryTransactionError
from ....logging_setup import DevSynthLogger
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


class S3MemoryAdapter(StorageAdapter):
    """Store memory items in an S3 bucket."""

    backend_type = "s3"

    def __init__(self, bucket: str, client: S3Client | None = None):
        if boto3 is None:  # pragma: no cover - defensive
            raise ImportError("boto3 is required for S3MemoryAdapter") from _BOTO3_ERROR
        self.bucket = bucket
        self.client: S3Client = client or boto3.client("s3")

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
        data = json.dumps(
            {
                "id": item.id,
                "content": item.content,
                "memory_type": (
                    item.memory_type.value
                    if hasattr(item.memory_type, "value")
                    else item.memory_type
                ),
                "metadata": item.metadata,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
        )
        self.client.put_object(Bucket=self.bucket, Key=item.id, Body=data)
        return str(item.id)

    def retrieve(self, item_id: str) -> MemoryItem | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=item_id)
        except ClientError:
            return None
        data = json.loads(obj["Body"].read())
        memory_type = MemoryType(data["memory_type"])
        return MemoryItem(
            id=data["id"],
            content=data["content"],
            memory_type=memory_type,
            metadata=data.get("metadata", {}),
        )

    def search(self, query: Mapping[str, str | MemoryType]) -> list[MemoryItem]:
        items: list[MemoryItem] = []
        resp = self.client.list_objects_v2(Bucket=self.bucket)
        for obj in resp.get("Contents", []):
            item = self.retrieve(obj["Key"])
            if not item:
                continue
            match = True
            for key, value in query.items():
                if key == "type":
                    expected = (
                        value if isinstance(value, MemoryType) else MemoryType(value)
                    )
                    if item.memory_type != expected:
                        match = False
                        break
                elif item.metadata.get(key) != value:
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
