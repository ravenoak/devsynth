from devsynth.domain.interfaces.requirement import RequirementRepositoryInterface


class DummyRepo(RequirementRepositoryInterface):
    def get_requirement(self, requirement_id):
        raise NotImplementedError

    def get_all_requirements(self):
        raise NotImplementedError

    def save_requirement(self, requirement):
        raise NotImplementedError

    def delete_requirement(self, requirement_id):
        raise NotImplementedError
