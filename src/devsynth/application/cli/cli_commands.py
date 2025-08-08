"""Compatibility layer exposing CLI commands for testing."""

from __future__ import annotations

from devsynth.core import workflows

init_project = workflows.init_project

from .commands import (
    config_cmds,
    diagnostics_cmds,
    extra_cmds,
    generation_cmds,
    interface_cmds,
    pipeline_cmds,
)
from .commands import spec_cmd as _spec_module
from .registry import COMMAND_REGISTRY
from .utils import _check_services

generate_specs = _spec_module.generate_specs
_spec_module.generate_specs = generate_specs

for _name, _cmd in COMMAND_REGISTRY.items():
    globals()[f"{_name.replace('-', '_')}_cmd"] = _cmd

__all__ = [
    "workflows",
    "generate_specs",
    "_check_services",
] + [f"{name.replace('-', '_')}_cmd" for name in COMMAND_REGISTRY]
