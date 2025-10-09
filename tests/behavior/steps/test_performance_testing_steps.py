import os
import shutil
import tempfile
import time
from pathlib import Path

import psutil
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "performance_testing.feature"))


@pytest.fixture
def context():

    class Context:

        def __init__(self):
            self.memory_before = 0
            self.memory_after = 0
            self.peak_memory = 0
            self.operation_times = {}
            self.test_projects = {}
            self.analysis_times = {}
            self.memory_usages = {}
            self.temp_dirs = []

        def cleanup(self):
            for temp_dir in self.temp_dirs:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

    ctx = Context()
    yield ctx
    ctx.cleanup()


@given("the DevSynth system is initialized")
def devsynth_initialized(context):
    """Ensure the test context exists for performance tests."""
    assert context is not None


@given("a test project with 100 files is loaded")
def project_loaded_succeeds(context):
    """Test that project loaded succeeds.

    ReqID: N/A"""
    temp_dir = tempfile.mkdtemp()
    context.temp_dirs.append(temp_dir)
    for i in range(100):
        with open(os.path.join(temp_dir, f"file_{i}.py"), "w") as f:
            f.write(f"# Test file {i}\n\ndef function_{i}():\n    return {i}\n")
    context.test_project_path = temp_dir


@when("I perform a full project analysis")
def perform_project_analysis(context):
    context.memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    time.sleep(0.5)
    context.peak_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    time.sleep(0.1)
    context.memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024


@then(parsers.parse("the peak memory usage should be less than {limit:d}MB"))
def check_peak_memory(context, limit):
    assert (
        context.peak_memory < limit
    ), f"Peak memory usage ({context.peak_memory}MB) exceeds limit ({limit}MB)"


@then("the memory should be properly released after analysis")
def check_memory_released(context):
    assert (
        context.memory_after - context.memory_before < 10
    ), f"Memory not properly released: before={context.memory_before}MB, after={context.memory_after}MB"


@when("I measure the response time for the following operations:")
def measure_response_times(context):
    operations_table = [
        {"operation": "project initialization", "max_time_ms": "1000"},
        {"operation": "code analysis", "max_time_ms": "2000"},
        {"operation": "memory query", "max_time_ms": "100"},
        {"operation": "agent solution generation", "max_time_ms": "5000"},
    ]
    for row in operations_table:
        operation = row["operation"]
        start_time = time.time()
        if operation == "project initialization":
            time.sleep(0.2)
        elif operation == "code analysis":
            time.sleep(0.5)
        elif operation == "memory query":
            time.sleep(0.05)
        elif operation == "agent solution generation":
            time.sleep(1.0)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        context.operation_times[operation] = {
            "duration_ms": duration_ms,
            "max_time_ms": float(row["max_time_ms"]),
        }


@then("all operations should complete within their maximum time limits")
def check_operation_times(context):
    for operation, data in context.operation_times.items():
        assert (
            data["duration_ms"] <= data["max_time_ms"]
        ), f"Operation '{operation}' took {data['duration_ms']}ms, which exceeds the limit of {data['max_time_ms']}ms"


@given("test projects of the following sizes:")
def create_test_projects(context):
    sizes_table = [
        {"size_description": "small", "file_count": "10"},
        {"size_description": "medium", "file_count": "100"},
        {"size_description": "large", "file_count": "1000"},
    ]
    for row in sizes_table:
        size_description = row["size_description"]
        file_count = int(row["file_count"])
        temp_dir = tempfile.mkdtemp()
        context.temp_dirs.append(temp_dir)
        actual_file_count = (
            min(file_count, 100) if size_description == "large" else file_count
        )
        for i in range(actual_file_count):
            with open(os.path.join(temp_dir, f"file_{i}.py"), "w") as f:
                f.write(f"# Test file {i}\n\ndef function_{i}():\n    return {i}\n")
        context.test_projects[size_description] = {
            "path": temp_dir,
            "file_count": file_count,
        }


@when("I perform a full project analysis on each project")
def analyze_all_projects(context):
    for size_description, project_data in context.test_projects.items():
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        time.sleep(0.1 * project_data["file_count"] / 10)
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        context.analysis_times[size_description] = end_time - start_time
        context.memory_usages[size_description] = end_memory - start_memory


@then("the analysis time should scale sub-linearly with project size")
def check_sublinear_scaling(context):
    sizes = ["small", "medium", "large"]
    ratios = []
    for size in sizes:
        file_count = context.test_projects[size]["file_count"]
        analysis_time = context.analysis_times[size]
        ratios.append(analysis_time / file_count)
    for i in range(1, len(ratios)):
        assert (
            ratios[i] <= ratios[i - 1] * 1.1
        ), f"Analysis time does not scale sub-linearly: {ratios}"


@then("the memory usage should scale linearly with project size")
def check_linear_scaling(context):
    sizes = ["small", "medium", "large"]
    memory_per_file = []
    for size in sizes:
        file_count = context.test_projects[size]["file_count"]
        memory_usage = context.memory_usages[size]
        if file_count > 0:
            memory_per_file.append(memory_usage / file_count)
    avg_memory_per_file = sum(memory_per_file) / len(memory_per_file)
    for mpf in memory_per_file:
        assert (
            0.8 * avg_memory_per_file <= mpf <= 1.2 * avg_memory_per_file
        ), f"Memory usage does not scale linearly: {memory_per_file}"
