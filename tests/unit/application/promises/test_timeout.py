import pytest
import time
from devsynth.application.promises import PromiseAgent, PromiseBroker

@pytest.mark.medium
def test_promise_auto_reject_after_timeout_succeeds():
    """Test that promise auto reject after timeout succeeds.

ReqID: N/A"""
    broker = PromiseBroker()
    provider = PromiseAgent(agent_id='provider', broker=broker)

    def slow(delay: float) -> str:
        time.sleep(delay)
        return 'done'
    provider.register_capability(name='slow', handler_func=slow, description='slow op', parameters={'delay': 'float'})
    requester = PromiseAgent(agent_id='requester', broker=broker)
    promise = requester.request_capability(name='slow', timeout=0.3, delay=1)
    time.sleep(0.5)
    assert promise.is_rejected
    assert isinstance(promise.reason, TimeoutError)

@pytest.mark.medium
def test_timeout_timer_cancellation_on_fulfill_succeeds():
    """Test that timeout timer cancellation on fulfill succeeds.

ReqID: N/A"""
    broker = PromiseBroker()
    provider = PromiseAgent(agent_id='provider', broker=broker)
    provider.register_capability(name='fast', handler_func=lambda: 'ok', description='fast')
    requester = PromiseAgent(agent_id='requester', broker=broker)
    promise = requester.request_capability(name='fast', timeout=0.3)
    provider.handle_pending_capabilities()
    time.sleep(0.5)
    assert promise.is_fulfilled
    assert promise.value == 'ok'