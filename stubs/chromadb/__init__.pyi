from typing import Any, Mapping, Protocol, Sequence

class CollectionProtocol(Protocol):
    def add(
        self,
        *,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, Any]],
        documents: Sequence[Any],
    ) -> Any: ...
    def get(
        self, ids: Sequence[str] | None = ..., include: Sequence[str] | None = ...
    ) -> Mapping[str, Any]: ...
    def delete(self, ids: Sequence[str]) -> Any: ...
    def query(
        self,
        *,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int,
        include: Sequence[str],
    ) -> Mapping[str, Any]: ...

class PersistentClient:
    def __init__(self, path: str) -> None: ...
    def get_or_create_collection(self, name: str) -> CollectionProtocol: ...

class EphemeralClient:
    def __init__(self, settings: Any) -> None: ...
    def get_or_create_collection(self, name: str) -> CollectionProtocol: ...
