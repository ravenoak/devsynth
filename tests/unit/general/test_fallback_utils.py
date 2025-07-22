import threading
import time

import pytest

from devsynth.fallback import Bulkhead, CircuitBreaker
from devsynth.exceptions import DevSynthError


def test_bulkhead_limits_concurrency():
    """Bulkhead restricts concurrent calls under load. ReqID: N/A"""
    bulkhead = Bulkhead(max_concurrent_calls=2, max_queue_size=1)
    active = 0
    max_active = 0
    lock = threading.Lock()
    results = []
    errors = []

    @bulkhead
    def guarded():
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        try:
            time.sleep(0.1)
            return True
        finally:
            with lock:
                active -= 1

    def worker():
        try:
            results.append(guarded())
        except DevSynthError as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert max_active <= 2
    assert len(results) == 3
    assert len(errors) == 1


def test_circuit_breaker_concurrent_failures():
    """Circuit breaker opens after concurrent failures. ReqID: N/A"""
    cb = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.2,
        test_calls=1,
        exception_types=(ValueError,),
    )
    errors = []

    @cb
    def always_fail():
        raise ValueError("boom")

    def worker():
        try:
            always_fail()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert cb.state == cb.OPEN
    assert len(errors) == 2
    with pytest.raises(DevSynthError):
        always_fail()

    time.sleep(0.2)

    @cb
    def success():
        return "ok"

    assert success() == "ok"
    assert cb.state == cb.CLOSED
