from __future__ import annotations

from typing import Any

from .exceptions import VerifyMismatchError

__all__ = ["PasswordHasher", "VerifyMismatchError"]

class PasswordHasher:
    def __init__(
        self,
        *,
        time_cost: int = ...,
        memory_cost: int = ...,
        parallelism: int = ...,
        hash_len: int = ...,
        salt_len: int = ...,
    ) -> None: ...
    def hash(self, password: str) -> str: ...
    def verify(self, hashed_password: str, password: str) -> bool: ...
