from unittest.mock import MagicMock, patch

import pytest

from devsynth.adapters.orchestration.langgraph_adapter import LangGraphWorkflowEngine
from devsynth.domain.models.workflow import WorkflowStatus, WorkflowStep


@pytest.fixture
def engine():
    return LangGraphWorkflowEngine()


@pytest.mark.fast
def test_graph_transitions_complete(engine):
    wf = engine.create_workflow("wf", "desc")
    step1 = WorkflowStep(id="s1", name="Step 1", description="d1", agent_type="t")
    step2 = WorkflowStep(id="s2", name="Step 2", description="d2", agent_type="t")
    wf = engine.add_step(wf, step1)
    wf = engine.add_step(wf, step2)

    # Patch orchestration to be a no-op that appends a message
    class FakeService:
        def process_step(self, state, step):
            state.messages.append({"role": "system", "content": f"ran {step.id}"})
            return state

    with patch(
        "devsynth.orchestration.step_executor.OrchestrationService", FakeService
    ):
        result = engine.execute_workflow(wf, context={})

    assert result.status == WorkflowStatus.COMPLETED


@pytest.mark.fast
def test_failure_branch_sets_failed(engine):
    wf = engine.create_workflow("wf", "desc")
    step1 = WorkflowStep(id="s1", name="Step 1", description="d1", agent_type="t")
    wf = engine.add_step(wf, step1)

    class FailingService:
        def process_step(self, state, step):
            raise RuntimeError("boom")

    with patch(
        "devsynth.orchestration.step_executor.OrchestrationService", FailingService
    ):
        result = engine.execute_workflow(wf, context={})

    assert result.status == WorkflowStatus.FAILED


@pytest.mark.fast
def test_retry_branch_succeeds_with_max_retries(engine):
    wf = engine.create_workflow("wf", "desc")
    step1 = WorkflowStep(id="s1", name="Step 1", description="d1", agent_type="t")
    wf = engine.add_step(wf, step1)

    calls = {"n": 0}

    class FlakyService:
        def process_step(self, state, step):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("transient")
            state.messages.append({"role": "system", "content": "ok"})
            return state

    with patch(
        "devsynth.orchestration.step_executor.OrchestrationService", FlakyService
    ):
        # Allow one retry
        result = engine.execute_workflow(wf, context={"max_retries": 1})

    assert calls["n"] == 2
    assert result.status == WorkflowStatus.COMPLETED


@pytest.mark.fast
def test_streaming_callback_called(engine):
    wf = engine.create_workflow("wf", "desc")
    step1 = WorkflowStep(id="s1", name="Step 1", description="d1", agent_type="t")
    wf = engine.add_step(wf, step1)

    class Service:
        def process_step(self, state, step):
            state.messages.append({"role": "agent", "content": "result"})
            return state

    stream_events = []

    def stream_cb(evt):
        stream_events.append(evt)

    with patch("devsynth.orchestration.step_executor.OrchestrationService", Service):
        result = engine.execute_workflow(wf, context={"stream_callback": stream_cb})

    assert result.status == WorkflowStatus.COMPLETED
    # We expect at least a step_started and a message event
    kinds = {e.get("event") for e in stream_events}
    assert "step_started" in kinds
    assert "message" in kinds


@pytest.mark.fast
def test_cancellation_pauses_before_first_step(engine):
    wf = engine.create_workflow("wf", "desc")
    step1 = WorkflowStep(id="s1", name="Step 1", description="d1", agent_type="t")
    wf = engine.add_step(wf, step1)

    spy = MagicMock()

    class SpyService:
        def process_step(self, state, step):
            spy()
            return state

    with patch("devsynth.orchestration.step_executor.OrchestrationService", SpyService):
        result = engine.execute_workflow(wf, context={"is_cancelled": lambda: True})

    assert result.status == WorkflowStatus.PAUSED
    spy.assert_not_called()
