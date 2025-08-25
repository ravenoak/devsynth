import os
from uuid import uuid4

import pytest

from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
    RequirementPriority,
)


class StubLLM:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def query(self, prompt: str) -> str:
        self.calls.append(prompt)
        # Route by simple prompt hints
        if "Determine if the following reasoning reaches consensus" in prompt:
            return "yes"
        return self.responses.get(prompt, self.responses.get("*", "ok"))


class StubReqRepo:
    def __init__(self, req_map=None, all_reqs=None):
        self.req_map = req_map or {}
        self.all_reqs = all_reqs or []

    def get_requirement(self, rid):
        return self.req_map.get(rid)

    def get_all_requirements(self):
        return self.all_reqs


class StubReasoningRepo:
    def __init__(self):
        self.saved = None

    def get_reasoning_for_change(self, cid):
        return None

    def save_reasoning(self, reasoning):
        self.saved = reasoning
        return reasoning


class StubImpactRepo:
    def __init__(self):
        self.saved = None

    def get_impact_assessment_for_change(self, cid):
        return None

    def save_impact_assessment(self, assessment):
        self.saved = assessment
        return assessment


class StubChatRepo:
    def save_session(self, session):
        return session

    def get_session(self, sid):
        class S:
            def __init__(self, sid):
                self.id = sid
                self.messages = []

                def add_message(sender, content):
                    return None

            def add_message(self, sender, content):
                class M:
                    def __init__(self, sender, content):
                        self.sender = sender
                        self.content = content

                m = M(sender, content)
                self.messages.append(m)
                return m

        return S(sid)

    def save_message(self, msg):
        return msg


class StubNotification:
    def notify_impact_assessment_completed(self, assessment):
        return None


class StubMemory:
    def __init__(self):
        self.calls = []

    def store_with_edrr_phase(self, data, memory_type, edrr_phase, metadata):
        self.calls.append(
            {"edrr_phase": edrr_phase, "metadata": metadata, "type": memory_type}
        )


@pytest.fixture(autouse=True)
def deterministic_env(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_DETERMINISTIC_REASONING", "1")


def make_service(llm=None, req_repo=None, mem=None):
    return DialecticalReasonerService(
        requirement_repository=req_repo or StubReqRepo(),
        reasoning_repository=StubReasoningRepo(),
        impact_repository=StubImpactRepo(),
        chat_repository=StubChatRepo(),
        notification_service=StubNotification(),
        llm_service=llm or StubLLM(responses={"*": "ok"}),
        memory_manager=mem or StubMemory(),
    )


def test_identify_affected_components_deterministic():
    rid = uuid4()
    req = Requirement(id=rid, metadata={"component": "B"})
    change = RequirementChange(requirement_id=rid)
    # new state with another component
    change.new_state = Requirement(id=uuid4(), metadata={"component": "A"})

    service = make_service(req_repo=StubReqRepo(req_map={rid: req}))
    comps = service._identify_affected_components(change)
    assert comps == [
        "A",
        "B",
    ], "Components should be unique and sorted deterministically"


def test_identify_affected_requirements_deterministic():
    rid = uuid4()
    dep1 = Requirement(id=uuid4(), dependencies=[rid])
    dep2 = Requirement(id=uuid4(), dependencies=[rid])
    change = RequirementChange(requirement_id=rid)
    # Order in repo doesn't matter; expect deterministic sorted by UUID string
    repo = StubReqRepo(all_reqs=[dep2, dep1])
    service = make_service(req_repo=repo)
    ids = service._identify_affected_requirements(change)
    assert ids == sorted(ids, key=lambda u: str(u))
    # first one should be the changed requirement id
    assert str(ids[0]) <= min(str(dep1.id), str(dep2.id))


def test_generate_arguments_sorted(monkeypatch):
    # Reverse order in text, expect sorted by position/content
    text = (
        "Argument 2\n"
        "Position: AGAINST\n"
        "Content: zeta\n"
        "Counterargument: aaa\n\n"
        "Argument 1\n"
        "Position: FOR\n"
        "Content: alpha\n"
        "Counterargument: bbb\n"
    )

    class LL(StubLLM):
        def query(self, prompt: str) -> str:
            if "Arguments" in prompt or "arguments" in prompt:
                return text
            if "Determine if the following reasoning" in prompt:
                return "yes"
            return "ok"

    service = make_service(llm=LL())
    change = RequirementChange(requirement_id=uuid4(), change_type=ChangeType.ADD)
    change.new_state = Requirement(title="T", description="D")
    args = service._generate_arguments(change, "t", "a")
    # After sorting, FOR/alpha should come before AGAINST/zeta
    assert args[0]["content"].lower() == "alpha"
    assert args[1]["content"].lower() == "zeta"


def test_edrr_phase_mapping_on_persist():
    rid = uuid4()
    mem = StubMemory()

    # LLM returns minimal values for thesis/antithesis/etc and consensus yes
    class LL(StubLLM):
        def query(self, prompt: str) -> str:
            if "Determine if the following reasoning" in prompt:
                return "yes"
            return "ok"

    service = make_service(llm=LL(), req_repo=StubReqRepo(), mem=mem)

    # ADD -> EXPAND
    change_add = RequirementChange(requirement_id=rid, change_type=ChangeType.ADD)
    change_add.new_state = Requirement(title="Add", description="desc")
    service.evaluate_change(change_add)
    assert any(
        c["edrr_phase"] == "EXPAND" for c in mem.calls
    ), "ADD should map to EXPAND phase"

    # REMOVE -> RETROSPECT
    mem.calls.clear()
    change_remove = RequirementChange(requirement_id=rid, change_type=ChangeType.REMOVE)
    change_remove.previous_state = Requirement(title="Del", description="desc")
    service.assess_impact(change_remove)
    assert any(
        c["edrr_phase"] == "RETROSPECT" for c in mem.calls
    ), "REMOVE should map to RETROSPECT phase"

    # MODIFY stays REFINE
    mem.calls.clear()
    change_mod = RequirementChange(requirement_id=rid, change_type=ChangeType.MODIFY)
    change_mod.previous_state = Requirement(title="Prev", description="desc")
    change_mod.new_state = Requirement(title="New", description="desc")
    service.evaluate_change(change_mod)
    assert any(
        c["edrr_phase"] == "REFINE" for c in mem.calls
    ), "MODIFY should stay REFINE"


def test_evaluation_hook_invoked_on_consensus_true():
    rid = uuid4()
    mem = StubMemory()

    class LL(StubLLM):
        def query(self, prompt: str) -> str:
            if "Determine if the following reasoning" in prompt:
                return "yes"
            return "ok"

    service = make_service(llm=LL(), req_repo=StubReqRepo(), mem=mem)
    calls = []

    def hook(reasoning, consensus):
        calls.append({"rid": reasoning.change_id, "consensus": consensus})

    service.register_evaluation_hook(hook)
    change = RequirementChange(requirement_id=rid, change_type=ChangeType.MODIFY)
    change.previous_state = Requirement(title="Prev", description="desc")
    change.new_state = Requirement(title="Mod", description="desc")
    service.evaluate_change(change)

    assert calls, "Hook should have been invoked"
    assert calls[-1]["consensus"] is True
