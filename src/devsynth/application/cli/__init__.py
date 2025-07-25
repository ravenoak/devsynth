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
    init_cmd,
    spec_cmd,
    test_cmd,
    code_cmd,
    run_pipeline_cmd,
    config_cmd,
    enable_feature_cmd,
    gather_cmd,
    config_app,
    inspect_cmd,
    webapp_cmd,
    webui_cmd,
    dbschema_cmd,
    doctor_cmd,
    check_cmd,
    refactor_cmd,
    serve_cmd,
)

# Import commands from the commands directory
from .commands.inspect_code_cmd import inspect_code_cmd
from .commands.edrr_cycle_cmd import edrr_cycle_cmd

# Import ingest_cmd
from .ingest_cmd import ingest_cmd

__all__ = [
    "init_cmd",
    "spec_cmd",
    "test_cmd",
    "code_cmd",
    "run_pipeline_cmd",
    "config_cmd",
    "enable_feature_cmd",
    "gather_cmd",
    "config_app",
    "inspect_cmd",
    "webapp_cmd",
    "webui_cmd",
    "dbschema_cmd",
    "doctor_cmd",
    "check_cmd",
    "refactor_cmd",
    "serve_cmd",
    "inspect_code_cmd",
    "edrr_cycle_cmd",
    "ingest_cmd",
]
