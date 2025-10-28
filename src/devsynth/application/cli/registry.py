from __future__ import annotations

from typing import Dict
from collections.abc import Callable

COMMAND_REGISTRY: dict[str, Callable] = {}


def register(name: str, fn: Callable) -> None:
    """Register a CLI command.

    Args:
        name: Command name as used on the CLI.
        fn: Function implementing the command.
    """
    COMMAND_REGISTRY[name] = fn
