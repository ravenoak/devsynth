from __future__ import annotations

from typing import Any

class Prompt:
    @classmethod
    def ask(cls, prompt: str, *args: Any, **kwargs: Any) -> str: ...

class Confirm:
    @classmethod
    def ask(cls, prompt: str, *args: Any, **kwargs: Any) -> bool: ...
