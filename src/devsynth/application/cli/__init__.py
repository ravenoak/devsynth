"""
Application-level CLI facades that delegate into orchestration layer.
Each function contains only I/O & user interaction concerns.
"""
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Import commands from cli_commands.py
from .cli_commands import (
    init_cmd, spec_cmd, test_cmd, code_cmd, run_cmd, config_cmd,
    analyze_cmd, webapp_cmd, dbschema_cmd, adaptive_cmd
)

# Import commands from the commands directory
from .commands.analyze_code_cmd import analyze_code_cmd

__all__ = [
    "init_cmd", "spec_cmd", "test_cmd", "code_cmd", "run_cmd", "config_cmd",
    "analyze_cmd", "webapp_cmd", "dbschema_cmd", "adaptive_cmd", "analyze_code_cmd"
]
