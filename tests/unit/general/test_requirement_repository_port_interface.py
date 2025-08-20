from uuid import uuid4

import pytest

from devsynth.domain.models.requirement import Requirement
from devsynth.ports.requirement_port import RequirementRepositoryPort
from tests.fixtures.dummy_requirement_port import DummyPort


def test_requirement_repository_port_is_abstract():
    with pytest.raises(TypeError):
        RequirementRepositoryPort()


@pytest.mark.fast
def test_dummy_requirement_port_methods_raise_not_implemented():
    port = DummyPort()
    requirement_id = uuid4()
    requirement = Requirement(title="Test requirement")
    with pytest.raises(NotImplementedError):
        port.get_requirement(requirement_id)
    with pytest.raises(NotImplementedError):
        port.get_all_requirements()
    with pytest.raises(NotImplementedError):
        port.save_requirement(requirement)
    with pytest.raises(NotImplementedError):
        port.delete_requirement(requirement_id)
