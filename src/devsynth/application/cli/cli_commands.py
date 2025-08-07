"""Compatibility layer exposing CLI commands for testing."""

from __future__ import annotations

from devsynth.core import workflows

from .command_registry import COMMAND_REGISTRY
from .commands import spec_cmd as _spec_module

generate_specs = _spec_module.generate_specs
_spec_module.generate_specs = generate_specs

# Export command functions as module-level names for tests
for _name, _cmd in COMMAND_REGISTRY.items():
    globals()[f"{_name.replace('-', '_')}_cmd"] = _cmd


def _check_services(*_, **__):
    """Placeholder service check used in tests."""
    return True


__all__ = [
    "workflows",
    "generate_specs",
    "_check_services",
] + [f"{name.replace('-', '_')}_cmd" for name in COMMAND_REGISTRY]
