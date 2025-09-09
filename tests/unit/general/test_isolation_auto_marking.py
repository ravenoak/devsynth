import pytest


class MockItem:
    def __init__(self, name, nodeid="", fixturenames=None, markers=None):
        self.name = name
        self.nodeid = nodeid or name
        self.fixturenames = list(fixturenames or [])
        self._markers = list(markers or [])

    def iter_markers(self, name=None):
        if name is None:
            return list(self._markers)
        return [m for m in self._markers if getattr(m, "name", None) == name]

    def get_closest_marker(self, name):
        for m in self._markers:
            if getattr(m, "name", None) == name:
                return m
        return None

    def add_marker(self, marker):
        # pytest's mark objects have a .name attribute when attached via pytest.mark.<name>
        self._markers.append(marker)

    @property
    def markers(self):
        return {getattr(m, "name", None) for m in self._markers}


class MockConfig:
    pass


@pytest.mark.fast
def test_auto_isolation_for_tmp_path_fixture():
    from tests.conftest import pytest_collection_modifyitems

    item = MockItem("test_writes_files", fixturenames={"tmp_path"})
    pytest_collection_modifyitems(MockConfig(), [item])
    assert "isolation" in item.markers, "Expected isolation mark when tmp_path is used"


@pytest.mark.fast
def test_auto_isolation_for_network_keyword():
    from tests.conftest import pytest_collection_modifyitems

    item = MockItem(
        "test_network_call",
        nodeid="tests/unit/foo/test_network_call.py::test_network_call",
    )
    pytest_collection_modifyitems(MockConfig(), [item])
    assert (
        "isolation" in item.markers
    ), "Expected isolation mark for network-related test name"
