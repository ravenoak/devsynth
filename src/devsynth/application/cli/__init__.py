"""Application-level CLI facades that delegate into orchestration layer."""

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

# Import modules so they register their commands
from .commands import (
    config_cmds,
    diagnostics_cmds,
    extra_cmds,
    generation_cmds,
    interface_cmds,
    pipeline_cmds,
)
from .commands.config_cmds import config_app
from .commands.inspect_code_cmd import inspect_code_cmd
from .ingest_cmd import ingest_cmd
from .registry import COMMAND_REGISTRY

# Re-export commands from registry as module-level functions
globals().update(
    {f"{name.replace('-', '_')}_cmd": fn for name, fn in COMMAND_REGISTRY.items()}
)

__all__ = [
    "config_app",
    "inspect_code_cmd",
    "ingest_cmd",
    "COMMAND_REGISTRY",
] + [f"{name.replace('-', '_')}_cmd" for name in COMMAND_REGISTRY]
