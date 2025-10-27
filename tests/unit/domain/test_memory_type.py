import json

import pytest

from devsynth.domain.models.memory import MemoryType


@pytest.mark.medium
def test_memory_type_serialization_deserialization():
    """Ensure all MemoryType members serialize and deserialize correctly.

    ReqID: DEV-0000"""
    for name, member in MemoryType.__members__.items():
        serialized = json.dumps(member.value)
        deserialized_value = json.loads(serialized)
        assert deserialized_value == member.value
        assert MemoryType(deserialized_value) is member


@pytest.mark.medium
def test_working_memory_alias():
    """Alias WORKING_MEMORY should reference the same member as WORKING.

    ReqID: DEV-0000"""
    assert MemoryType.WORKING_MEMORY is MemoryType.WORKING


@pytest.mark.medium
def test_memory_type_members_complete():
    """Verify that all expected memory types are present.

    ReqID: DEV-0000"""
    expected = [
        "SHORT_TERM",
        "LONG_TERM",
        "WORKING",
        "EPISODIC",
        "SOLUTION",
        "DIALECTICAL_REASONING",
        "TEAM_STATE",
        "KNOWLEDGE_GRAPH",
        "RELATIONSHIP",
        "CODE_ANALYSIS",
        "CODE",
        "CODE_TRANSFORMATION",
        "DOCUMENTATION",
        "CONTEXT",
        "CONVERSATION",
        "TASK_HISTORY",
        "KNOWLEDGE",
        "ERROR_LOG",
        "COLLABORATION_TASK",
        "COLLABORATION_MESSAGE",
        "COLLABORATION_TEAM",
        "PEER_REVIEW",
        "EXPAND_RESULTS",
        "DIFFERENTIATE_RESULTS",
        "REFINE_RESULTS",
        "RETROSPECT_RESULTS",
        "FINAL_REPORT",
        "EDRR_CYCLE_RESULTS",
        "INGEST_EXPAND_RESULTS",
        "INGEST_DIFFERENTIATE_RESULTS",
        "INGEST_REFINE_RESULTS",
        "INGEST_RETROSPECT_RESULTS",
    ]
    assert [member.name for member in MemoryType] == expected


@pytest.mark.parametrize("value", [m.value for m in MemoryType])
@pytest.mark.medium
def test_memory_type_lookup_by_value(value):
    """Ensure enum members can be retrieved from their values.

    ReqID: DEV-0000"""
    assert MemoryType(value).value == value
