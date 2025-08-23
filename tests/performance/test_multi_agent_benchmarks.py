"""Hypothesis-based multi-agent workload benchmarks. ReqID: PERF-15"""

import pytest

pytest.importorskip("hypothesis")
pytest.importorskip("pytest_benchmark")
pytest.importorskip("pytest_benchmark.plugin")

from hypothesis import given
from hypothesis import strategies as st


@given(
    num_agents=st.integers(min_value=1, max_value=8),
    workload=st.integers(min_value=1, max_value=100),
)
@pytest.mark.medium
def test_multi_agent_workload_benchmark(benchmark, num_agents, workload):
    """Benchmark workload distribution across agents. ReqID: PERF-15"""
    from math import ceil

    def simulate():
        tasks_per_agent = ceil(workload / num_agents)
        for _ in range(num_agents):
            for _ in range(tasks_per_agent):
                pass

    benchmark(simulate)
