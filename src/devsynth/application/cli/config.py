"""Shared configuration objects for CLI commands."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class CLIConfig:
    """Configuration options for CLI interactions.

    Attributes
    ----------
    non_interactive:
        When ``True`` commands should avoid interactive prompts and rely on
        provided defaults instead.
    """

    non_interactive: bool = False

    @classmethod
    def from_env(cls) -> CLIConfig:
        """Create a configuration populated from environment variables."""

        val = os.environ.get("DEVSYNTH_NONINTERACTIVE", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        return cls(non_interactive=val)


__all__ = ["CLIConfig"]
