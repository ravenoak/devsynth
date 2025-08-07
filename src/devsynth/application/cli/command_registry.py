"""Registry of CLI command functions."""

from __future__ import annotations

from .commands.code_cmd import code_cmd
from .commands.completion_cmd import completion_cmd
from .commands.config_cmd import config_app, config_cmd, enable_feature_cmd
from .commands.dbschema_cmd import dbschema_cmd
from .commands.doctor_cmd import doctor_cmd
from .commands.dpg_cmd import dpg_cmd
from .commands.edrr_cycle_cmd import edrr_cycle_cmd
from .commands.gather_cmd import gather_cmd
from .commands.init_cmd import init_cmd
from .commands.inspect_cmd import inspect_cmd
from .commands.refactor_cmd import refactor_cmd
from .commands.run_pipeline_cmd import run_pipeline_cmd
from .commands.run_tests_cmd import run_tests_cmd
from .commands.serve_cmd import serve_cmd
from .commands.spec_cmd import spec_cmd
from .commands.test_cmd import test_cmd
from .commands.webapp_cmd import webapp_cmd
from .commands.webui_cmd import webui_cmd

COMMAND_REGISTRY = {
    "spec": spec_cmd,
    "test": test_cmd,
    "code": code_cmd,
    "run-pipeline": run_pipeline_cmd,
    "config": config_cmd,
    "enable-feature": enable_feature_cmd,
    "gather": gather_cmd,
    "refactor": refactor_cmd,
    "inspect": inspect_cmd,
    "webapp": webapp_cmd,
    "serve": serve_cmd,
    "dbschema": dbschema_cmd,
    "doctor": doctor_cmd,
    "check": doctor_cmd,
    "webui": webui_cmd,
    "dpg": dpg_cmd,
    "completion": completion_cmd,
    "init": init_cmd,
    "run-tests": run_tests_cmd,
    "edrr-cycle": edrr_cycle_cmd,
}


__all__ = [
    "code_cmd",
    "config_app",
    "config_cmd",
    "enable_feature_cmd",
    "dbschema_cmd",
    "dpg_cmd",
    "gather_cmd",
    "inspect_cmd",
    "refactor_cmd",
    "run_pipeline_cmd",
    "serve_cmd",
    "spec_cmd",
    "test_cmd",
    "webapp_cmd",
    "webui_cmd",
    "doctor_cmd",
    "check_cmd",
    "init_cmd",
    "run_tests_cmd",
    "edrr_cycle_cmd",
    "completion_cmd",
    "COMMAND_REGISTRY",
]

check_cmd = doctor_cmd
