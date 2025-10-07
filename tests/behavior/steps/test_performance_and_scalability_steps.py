"""BDD step implementations for performance and scalability testing."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from devsynth.testing.performance import (
    capture_baseline_metrics,
    capture_scalability_metrics,
)
from tests.behavior.feature_paths import feature_path


class Context:
    """Mutable state shared across performance and scalability steps."""

    def __init__(self) -> None:
        self.workload = 0
        self.baseline_result = None
        self.scalability_results = None
        self.baseline_path = Path("docs/performance/baseline_metrics.json")
        self.scalability_path = Path("docs/performance/scalability_metrics.json")
        self.baseline_backup = None
        self.scalability_backup = None

    def cleanup(self) -> None:
        if self.baseline_backup is not None:
            self.baseline_path.write_text(self.baseline_backup)
        elif self.baseline_path.exists():
            self.baseline_path.unlink()
        if self.scalability_backup is not None:
            self.scalability_path.write_text(self.scalability_backup)
        elif self.scalability_path.exists():
            self.scalability_path.unlink()


@scenario(
    feature_path(__file__, "general", "performance_and_scalability_testing.feature"),
    "baseline metrics are captured",
)
@pytest.mark.slow
def test_baseline_metrics_are_captured() -> None:
    """BDD scenario for generating baseline metrics."""


@scenario(
    feature_path(__file__, "general", "performance_and_scalability_testing.feature"),
    "baseline throughput is calculated",
)
@pytest.mark.slow
def test_baseline_throughput_is_calculated() -> None:
    """BDD scenario for validating throughput calculations."""


@scenario(
    feature_path(__file__, "general", "performance_and_scalability_testing.feature"),
    "baseline duration is recorded",
)
@pytest.mark.slow
def test_baseline_duration_is_recorded() -> None:
    """BDD scenario for persisting baseline task duration."""


@scenario(
    feature_path(__file__, "general", "performance_and_scalability_testing.feature"),
    "scalability metrics are captured for varying workloads",
)
@pytest.mark.slow
def test_scalability_metrics_are_captured_for_varying_workloads() -> None:
    """BDD scenario outline for capturing metrics across workloads."""


@scenario(
    feature_path(__file__, "general", "performance_and_scalability_testing.feature"),
    "scalability metrics file is created",
)
@pytest.mark.slow
def test_scalability_metrics_file_is_created() -> None:
    """BDD scenario for writing scalability metrics to disk."""


@scenario(
    feature_path(__file__, "general", "performance_and_scalability_testing.feature"),
    "scalability throughput is calculated",
)
@pytest.mark.slow
def test_scalability_throughput_is_calculated() -> None:
    """BDD scenario for recording scalability throughput."""


@pytest.fixture
def context() -> Iterator[Context]:
    """Provide an isolated context for scenario execution."""

    ctx = Context()
    yield ctx
    ctx.cleanup()


@given("the project environment is prepared")
def project_environment_prepared() -> None:
    Path("docs/performance").mkdir(parents=True, exist_ok=True)


@given("performance results are cleared")
def performance_results_cleared(context: Context) -> None:
    if context.baseline_path.exists():
        context.baseline_backup = context.baseline_path.read_text()
        context.baseline_path.unlink()
    if context.scalability_path.exists():
        context.scalability_backup = context.scalability_path.read_text()
        context.scalability_path.unlink()


@given(parsers.parse("a workload of {workload:d} operations"))
def set_workload(context: Context, workload: int) -> None:
    context.workload = workload


@when("the baseline performance task runs")
def run_baseline_task(context: Context) -> None:
    context.baseline_result = capture_baseline_metrics(
        context.workload, output_path=context.baseline_path
    )


@when("the scalability performance task runs")
def run_scalability_task(context: Context) -> None:
    workloads = [10000, 100000, 1000000]
    context.scalability_results = capture_scalability_metrics(
        workloads, output_path=context.scalability_path
    )


@then(parsers.parse('a metrics file "{path}" is created'))
def metrics_file_created(path: str) -> None:
    assert Path(path).exists(), f"{path} was not created"


@then(parsers.parse("the results include an entry for {workload:d}"))
def results_include_entry(context: Context, workload: int) -> None:
    assert any(r["workload"] == workload for r in context.scalability_results)


@then(parsers.parse('the metrics file "{path}" includes throughput'))
def metrics_file_includes_throughput(path: str) -> None:
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        assert all(
            entry.get("throughput_ops_per_s", 0) > 0 for entry in data
        ), "throughput missing for one or more entries"
    else:
        assert "throughput_ops_per_s" in data and data["throughput_ops_per_s"] > 0


@then(parsers.parse('the metrics file "{path}" includes duration'))
def metrics_file_includes_duration(path: str) -> None:
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        assert all(
            entry.get("duration_seconds", 0) > 0 for entry in data
        ), "duration missing for one or more entries"
    else:
        assert "duration_seconds" in data and data["duration_seconds"] > 0
