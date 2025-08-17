import pytest

from devsynth.domain.interfaces.requirement import RequirementRepositoryInterface
from devsynth.domain.models.requirement import Requirement


@pytest.mark.fast
def test_requirement_repository_interface_crud():
    repo = RequirementRepositoryInterface()
    req = Requirement(title="Test requirement")
    repo.save_requirement(req)
    assert repo.get_requirement(req.id) == req
    assert req in repo.get_all_requirements()
    assert repo.delete_requirement(req.id) is True
    assert repo.get_requirement(req.id) is None
