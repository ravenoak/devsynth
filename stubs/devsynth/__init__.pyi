from typing import Any as _Any

__all__: list[str]

# Allow unresolved attributes to defer to the runtime package.
def __getattr__(name: str) -> _Any: ...
