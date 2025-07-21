from uuid import UUID

import pytest

from devsynth.ports.requirement_port import RequirementRepositoryPort


class DummyPort(RequirementRepositoryPort):
    def get_requirement(self, requirement_id: UUID):
        raise NotImplementedError

    def get_all_requirements(self):
        raise NotImplementedError

    def save_requirement(self, requirement):
        raise NotImplementedError

    def delete_requirement(self, requirement_id: UUID):
        raise NotImplementedError
