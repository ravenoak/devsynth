from __future__ import annotations

from typing import Any, Self, Sequence

class _Widget:
    value: Any
    options: Sequence[Any]
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

class _Sidebar:
    selectbox: Sequence[_Widget]

class AppTest:
    title: Sequence[_Widget]
    sidebar: _Sidebar

    @classmethod
    def from_file(cls, path: Any, /, **kwargs: Any) -> Self: ...
    def run(self, **kwargs: Any) -> Self: ...
