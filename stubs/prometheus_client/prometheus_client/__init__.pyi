from __future__ import annotations

from collections.abc import Sequence


class CollectorRegistry:
    ...


class Counter:
    def __init__(self, name: str, documentation: str, labelnames: Sequence[str] | None = ...) -> None: ...

    def labels(self, **labels: str) -> Counter: ...

    def inc(self, amount: float = ...) -> None: ...


class Histogram:
    def __init__(self, name: str, documentation: str, labelnames: Sequence[str] | None = ...) -> None: ...

    def labels(self, **labels: str) -> Histogram: ...

    def observe(self, amount: float) -> None: ...


def generate_latest(registry: object | None = ...) -> bytes: ...


def start_http_server(port: int, addr: str = ...) -> None: ...


CONTENT_TYPE_LATEST: str

