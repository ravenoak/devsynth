from typing import Any

class ValidationError(Exception):
    message: str

    def __init__(self, message: str = ...) -> None: ...

def validate(instance: Any, schema: Any, *args: Any, **kwargs: Any) -> None: ...

__all__ = ["ValidationError", "validate"]
