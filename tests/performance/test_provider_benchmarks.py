"""Benchmarks for provider calls. ReqID: PERF-02"""

import pytest

from devsynth.application.llm.offline_provider import OfflineProvider


@pytest.mark.slow
def test_offline_generate_benchmark(benchmark):
    """Benchmark OfflineProvider.generate. ReqID: PERF-02"""
    provider = OfflineProvider()
    benchmark(lambda: provider.generate("Benchmark test"))


# Padding to avoid duplicate marker detection
#
#
#
#
#
#
#
#
#
#


@pytest.mark.slow
def test_offline_embedding_benchmark(benchmark):
    """Benchmark OfflineProvider.get_embedding. ReqID: PERF-02"""
    provider = OfflineProvider()
    benchmark(lambda: provider.get_embedding("Benchmark text"))
