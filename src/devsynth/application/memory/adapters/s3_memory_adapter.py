"""S3-backed memory adapter."""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from ....domain.models.memory import MemoryItem, MemoryType
from ....exceptions import MemoryTransactionError
from ....logging_setup import DevSynthLogger
from .storage_adapter import StorageAdapter

try:  # pragma: no cover - optional dependency
    import boto3
    from botocore.exceptions import ClientError
except Exception as exc:  # pragma: no cover - missing optional dependency
    boto3 = None  # type: ignore[assignment]
    ClientError = Exception  # type: ignore[misc]
    _BOTO3_ERROR = exc

logger = DevSynthLogger(__name__)


class S3MemoryAdapter(StorageAdapter):
    """Store memory items in an S3 bucket."""

    backend_type = "s3"

    def __init__(self, bucket: str, client: Any | None = None):
        if boto3 is None:  # pragma: no cover - defensive
            raise ImportError("boto3 is required for S3MemoryAdapter") from _BOTO3_ERROR
        self.bucket = bucket
        self.client = client or boto3.client("s3")

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
        return item.id

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
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

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        items: List[MemoryItem] = []
        resp = self.client.list_objects_v2(Bucket=self.bucket)
        for obj in resp.get("Contents", []):
            item = self.retrieve(obj["Key"])
            if not item:
                continue
            match = True
            for key, value in query.items():
                if key == "type":
                    if item.memory_type != value:
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
    def begin_transaction(self) -> str:  # pragma: no cover - simple
        raise MemoryTransactionError(
            "Transactions are not supported", store_type=self.backend_type
        )

    def commit_transaction(
        self, transaction_id: str
    ) -> bool:  # pragma: no cover - simple
        raise MemoryTransactionError(
            "Transactions are not supported",
            transaction_id=transaction_id,
            store_type=self.backend_type,
        )

    def rollback_transaction(
        self, transaction_id: str
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
