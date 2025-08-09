import pytest

from devsynth import metrics


def test_memory_metrics_increment_and_reset():
    metrics.reset_metrics()
    metrics.inc_memory("read")
    metrics.inc_memory("read")
    metrics.inc_memory("write")
    assert metrics.get_memory_metrics() == {"read": 2, "write": 1}
    metrics.reset_metrics()
    assert metrics.get_memory_metrics() == {}


def test_provider_and_retry_metrics():
    metrics.reset_metrics()
    metrics.inc_provider("openai")
    metrics.inc_retry("fetch")
    metrics.inc_retry_count("func")
    metrics.inc_retry_error("TimeoutError")
    assert metrics.get_provider_metrics() == {"openai": 1}
    assert metrics.get_retry_metrics() == {"fetch": 1}
    assert metrics.get_retry_count_metrics() == {"func": 1}
    assert metrics.get_retry_error_metrics() == {"TimeoutError": 1}
    metrics.reset_metrics()
    assert metrics.get_provider_metrics() == {}
    assert metrics.get_retry_metrics() == {}
    assert metrics.get_retry_count_metrics() == {}
    assert metrics.get_retry_error_metrics() == {}


def test_dashboard_metrics():
    metrics.reset_metrics()
    metrics.inc_dashboard("view")
    metrics.inc_dashboard("view")
    assert metrics.get_dashboard_metrics() == {"view": 2}
    metrics.reset_metrics()
    assert metrics.get_dashboard_metrics() == {}


def test_inc_memory_unhashable_raises_type_error():
    metrics.reset_metrics()
    with pytest.raises(TypeError):
        metrics.inc_memory([])  # type: ignore[arg-type]
