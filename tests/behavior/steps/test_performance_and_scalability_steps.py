from tests.behavior.feature_paths import feature_path
import json
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.testing.performance import (


    capture_baseline_metrics,
    capture_scalability_metrics,
)


pytestmark = [pytest.mark.medium]

scenarios(feature_path(__file__, "general", "performance_and_scalability_testing.feature"))


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.workload = 0
            self.baseline_result = None
            self.scalability_results = None
            self.baseline_path = Path("docs/performance/baseline_metrics.json")
            self.scalability_path = Path("docs/performance/scalability_metrics.json")
            self.baseline_backup = None
            self.scalability_backup = None

        def cleanup(self):
            if self.baseline_backup is not None:
                self.baseline_path.write_text(self.baseline_backup)
            elif self.baseline_path.exists():
                self.baseline_path.unlink()
            if self.scalability_backup is not None:
                self.scalability_path.write_text(self.scalability_backup)
            elif self.scalability_path.exists():
                self.scalability_path.unlink()

    ctx = Context()
    yield ctx
    ctx.cleanup()


@given("the project environment is prepared")
def project_environment_prepared():
    Path("docs/performance").mkdir(parents=True, exist_ok=True)


@given("performance results are cleared")
def performance_results_cleared(context):
    if context.baseline_path.exists():
        context.baseline_backup = context.baseline_path.read_text()
        context.baseline_path.unlink()
    if context.scalability_path.exists():
        context.scalability_backup = context.scalability_path.read_text()
        context.scalability_path.unlink()


@given(parsers.parse("a workload of {workload:d} operations"))
def set_workload(context, workload):
    context.workload = workload


@when("the baseline performance task runs")
def run_baseline_task(context):
    context.baseline_result = capture_baseline_metrics(
        context.workload, output_path=context.baseline_path
    )


@when("the scalability performance task runs")
def run_scalability_task(context):
    workloads = [10000, 100000, 1000000]
    context.scalability_results = capture_scalability_metrics(
        workloads, output_path=context.scalability_path
    )


@then(parsers.parse('a metrics file "{path}" is created'))
def metrics_file_created(path):
    assert Path(path).exists(), f"{path} was not created"


@then(parsers.parse("the results include an entry for {workload:d}"))
def results_include_entry(context, workload):
    assert any(r["workload"] == workload for r in context.scalability_results)


@then(parsers.parse('the metrics file "{path}" includes throughput'))
def metrics_file_includes_throughput(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        assert all(
            entry.get("throughput_ops_per_s", 0) > 0 for entry in data
        ), "throughput missing for one or more entries"
    else:
        assert "throughput_ops_per_s" in data and data["throughput_ops_per_s"] > 0


@then(parsers.parse('the metrics file "{path}" includes duration'))
def metrics_file_includes_duration(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        assert all(
            entry.get("duration_seconds", 0) > 0 for entry in data
        ), "duration missing for one or more entries"
    else:
        assert "duration_seconds" in data and data["duration_seconds"] > 0
