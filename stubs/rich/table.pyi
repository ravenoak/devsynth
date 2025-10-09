from __future__ import annotations

from typing import Any

from .console import RenderableType

class Table:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def add_column(self, header: str, **kwargs: Any) -> None: ...
    def add_row(self, *columns: RenderableType, **kwargs: Any) -> None: ...
