"""Register metrics-related CLI commands."""

from ..registry import register
from .alignment_metrics_cmd import alignment_metrics_cmd
from .test_metrics_cmd import test_metrics_cmd

register("alignment-metrics", alignment_metrics_cmd)
register("test-metrics", test_metrics_cmd)

__all__ = ["alignment_metrics_cmd", "test_metrics_cmd"]
