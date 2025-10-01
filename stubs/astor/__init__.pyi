from typing import Any

class _CodeGenModule:
    def to_source(self, node: Any) -> str: ...

def to_source(node: Any) -> str: ...

code_gen: _CodeGenModule

__all__ = ["to_source", "code_gen"]
