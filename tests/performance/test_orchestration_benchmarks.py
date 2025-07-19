"""Benchmarks for agent orchestration. ReqID: PERF-03"""

import os
from devsynth.application.orchestration.workflow import WorkflowManager


def test_workflow_execution_benchmark(benchmark, tmp_path):
    """Benchmark executing a simple workflow. ReqID: PERF-03"""
    os.environ["DEVSYNTH_WORKFLOWS_PATH"] = str(tmp_path / "workflows")
    os.environ["DEVSYNTH_CHECKPOINTS_PATH"] = str(tmp_path / "checkpoints")
    manager = WorkflowManager()

    def run() -> None:
        manager.execute_command("config", {})

    benchmark(run)
