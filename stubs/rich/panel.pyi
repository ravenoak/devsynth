from __future__ import annotations

from typing import Any

from .console import RenderableType

class Panel:
    def __init__(self, renderable: RenderableType, **kwargs: Any) -> None: ...
