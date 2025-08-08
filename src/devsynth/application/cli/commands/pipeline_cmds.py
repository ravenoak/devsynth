"""Commands that operate on the project pipeline."""

from ..registry import register
from .gather_cmd import gather_cmd
from .inspect_cmd import inspect_cmd
from .inspect_config_cmd import inspect_config_cmd
from .refactor_cmd import refactor_cmd
from .run_pipeline_cmd import run_pipeline_cmd

register("run-pipeline", run_pipeline_cmd)
register("gather", gather_cmd)
register("refactor", refactor_cmd)
register("inspect", inspect_cmd)
register("inspect-config", inspect_config_cmd)

__all__ = [
    "run_pipeline_cmd",
    "gather_cmd",
    "refactor_cmd",
    "inspect_cmd",
    "inspect_config_cmd",
]
