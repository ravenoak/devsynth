from __future__ import annotations

from typing import Any

from .console import RenderableType

class Tree:
    def __init__(self, label: RenderableType, **kwargs: Any) -> None: ...
    def add(self, label: RenderableType, **kwargs: Any) -> Tree: ...
