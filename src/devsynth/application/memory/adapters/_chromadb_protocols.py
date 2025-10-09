"""Structural typing helpers for optional ChromaDB dependencies."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, TypedDict


class ChromaGetResult(TypedDict, total=False):
    """Subset of fields returned by ``Collection.get``."""

    ids: list[str]
    embeddings: list[list[float]]
    metadatas: list[Mapping[str, object]]
    documents: list[object]


class ChromaQueryResult(TypedDict, total=False):
    """Subset of fields returned by ``Collection.query``."""

    ids: list[list[str]]
    embeddings: list[list[list[float]]]
    metadatas: list[list[Mapping[str, object]]]
    documents: list[list[object]]


class ChromaEmbeddingFunctionProtocol(Protocol):
    """Callable embedding function compatible with ChromaDB."""

    def __call__(self, inputs: Sequence[str]) -> Sequence[Sequence[float]]: ...


class ChromaCollectionProtocol(Protocol):
    """Structural protocol for the ChromaDB collection client."""

    def get(
        self, ids: Sequence[str] | None = ..., include: Sequence[str] | None = ...
    ) -> ChromaGetResult | None: ...

    def add(
        self,
        *,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, object]],
        documents: Sequence[object],
    ) -> object: ...

    def delete(self, *, ids: Sequence[str]) -> None: ...

    def query(
        self,
        *,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int,
        include: Sequence[str],
    ) -> ChromaQueryResult | None: ...


class ChromaClientProtocol(Protocol):
    """Structural protocol for ChromaDB client factories."""

    def get_or_create_collection(
        self,
        name: str,
        embedding_function: ChromaEmbeddingFunctionProtocol | None = ...,
    ) -> ChromaCollectionProtocol: ...


__all__ = [
    "ChromaClientProtocol",
    "ChromaCollectionProtocol",
    "ChromaEmbeddingFunctionProtocol",
    "ChromaGetResult",
    "ChromaQueryResult",
]
