from __future__ import annotations

from typing import Callable, Dict

COMMAND_REGISTRY: Dict[str, Callable] = {}


def register(name: str, fn: Callable) -> None:
    """Register a CLI command.

    Args:
        name: Command name as used on the CLI.
        fn: Function implementing the command.
    """
    COMMAND_REGISTRY[name] = fn
