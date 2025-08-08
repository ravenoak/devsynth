"""Additional CLI commands not part of primary groups."""

from ..registry import register
from .align_cmd import align_cmd
from .completion_cmd import completion_cmd
from .edrr_cycle_cmd import edrr_cycle_cmd
from .init_cmd import init_cmd
from .run_tests_cmd import run_tests_cmd

register("align", align_cmd)
register("completion", completion_cmd)
register("init", init_cmd)
register("run-tests", run_tests_cmd)
register("edrr-cycle", edrr_cycle_cmd)

__all__ = [
    "align_cmd",
    "completion_cmd",
    "init_cmd",
    "run_tests_cmd",
    "edrr_cycle_cmd",
]
