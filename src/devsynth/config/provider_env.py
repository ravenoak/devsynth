from __future__ import annotations

"""Typed environment configuration for provider-related flags.

This module centralizes parsing of provider environment variables with
consistent defaults. It is intentionally lightweight (dataclass + helpers)
so it can be safely imported by CLI and adapters without pulling heavy deps.

Guidelines:
- Offline-first defaults for test/CI flows
- Deterministic boolean parsing (1/true/yes/on)
- Non-intrusive: only write to environment when explicitly applied
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict

_TRUE_SET = {"1", "true", "yes", "on"}
_FALSE_SET = {"0", "false", "no", "off"}


@lru_cache(maxsize=32)
def _parse_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    s = str(val).strip().lower()
    if s in _TRUE_SET:
        return True
    if s in _FALSE_SET:
        return False
    return default


@dataclass(frozen=True)
class ProviderEnv:
    provider: str = "openai"
    offline: bool = False
    lmstudio_available: bool = False

    @classmethod
    def from_env(cls) -> ProviderEnv:
        return cls(
            provider=os.environ.get("DEVSYNTH_PROVIDER", "openai"),
            offline=_parse_bool(os.environ.get("DEVSYNTH_OFFLINE"), default=False),
            lmstudio_available=_parse_bool(
                os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"), default=False
            ),
        )

    def with_test_defaults(self) -> ProviderEnv:
        """Return a copy with safe defaults for tests/CI.

        - provider defaults to 'stub' if not explicitly set
        - offline defaults to True
        - lmstudio availability defaults to False unless explicitly set
        - ensure OPENAI_API_KEY has a deterministic placeholder when unset
        """
        # If provider was explicitly set, respect it; otherwise default to stub
        provider = os.environ.get("DEVSYNTH_PROVIDER", self.provider)
        if "DEVSYNTH_PROVIDER" not in os.environ:
            provider = "stub"
        # Offline default to true when unset
        offline = self.offline or ("DEVSYNTH_OFFLINE" not in os.environ)
        # LM Studio availability: default false when unset
        lmstudio = self.lmstudio_available  # already False by default when unset
        # Provide deterministic placeholder secrets for offline/stub paths
        os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
        return ProviderEnv(
            provider=provider, offline=offline, lmstudio_available=lmstudio
        )

    def apply_to_env(self) -> None:
        os.environ["DEVSYNTH_PROVIDER"] = self.provider
        os.environ["DEVSYNTH_OFFLINE"] = "true" if self.offline else "false"
        # Only set availability var when not already set to avoid overriding a user decision
        if "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" not in os.environ:
            os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = (
                "true" if self.lmstudio_available else "false"
            )

    def as_dict(self) -> dict[str, str]:
        return {
            "DEVSYNTH_PROVIDER": self.provider,
            "DEVSYNTH_OFFLINE": "true" if self.offline else "false",
            "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": (
                "true" if self.lmstudio_available else "false"
            ),
        }
