import json
from devsynth.domain.models.memory import MemoryType


def test_memory_type_serialization_deserialization():
    """Ensure all MemoryType members serialize and deserialize correctly."""
    for name, member in MemoryType.__members__.items():
        serialized = json.dumps(member.value)
        deserialized_value = json.loads(serialized)
        assert deserialized_value == member.value
        assert MemoryType(deserialized_value) is member


def test_working_memory_alias():
    """Alias WORKING_MEMORY should reference the same member as WORKING."""
    assert MemoryType.WORKING_MEMORY is MemoryType.WORKING
