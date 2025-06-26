import os
import pytest
from unittest.mock import patch

pytest.skip("Resource marker tests skipped", allow_module_level=True)


def test_is_lmstudio_available():
    """Test that is_lmstudio_available obeys environment variables and HTTP checks."""
    # Default: no env var -> not available and no request made
    with patch.dict(os.environ, {}, clear=True):
        with patch("requests.get") as mock_get:
            from tests.conftest import is_lmstudio_available

            assert not is_lmstudio_available()
            mock_get.assert_not_called()

    # Environment variable disabled
    with patch.dict(os.environ, {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "false"}):
        from tests.conftest import is_lmstudio_available

        assert not is_lmstudio_available()

    # Enabled with successful HTTP request
    with patch.dict(os.environ, {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "true"}):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            from tests.conftest import is_lmstudio_available

            assert is_lmstudio_available()

    # Enabled with failed HTTP request
    with patch.dict(os.environ, {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "true"}):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404
            from tests.conftest import is_lmstudio_available

            assert not is_lmstudio_available()

    # Enabled with exception
    with patch.dict(os.environ, {"DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "true"}):
        with patch("requests.get", side_effect=Exception("Connection error")):
            from tests.conftest import is_lmstudio_available

            assert not is_lmstudio_available()


def test_is_codebase_available():
    """Test that is_codebase_available checks environment variables and file existence."""
    # Test environment variable override
    with patch.dict(os.environ, {"DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE": "false"}):
        from tests.conftest import is_codebase_available

        assert not is_codebase_available()

    # Test directory exists
    with patch("pathlib.Path.exists", return_value=True):
        from tests.conftest import is_codebase_available

        assert is_codebase_available()

    # Test directory does not exist
    with patch("pathlib.Path.exists", return_value=False):
        from tests.conftest import is_codebase_available

        assert not is_codebase_available()


def test_is_cli_available():
    """Test that is_cli_available checks environment variables and CLI availability."""
    # Test environment variable override
    with patch.dict(os.environ, {"DEVSYNTH_RESOURCE_CLI_AVAILABLE": "false"}):
        from tests.conftest import is_cli_available

        assert not is_cli_available()

    # Test successful CLI command
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        from tests.conftest import is_cli_available

        assert is_cli_available()

    # Test failed CLI command
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        from tests.conftest import is_cli_available

        assert not is_cli_available()

    # Test exception during CLI command
    with patch("subprocess.run", side_effect=Exception("Command not found")):
        from tests.conftest import is_cli_available

        assert not is_cli_available()


def test_is_resource_available():
    """Test that is_resource_available calls the correct checker function."""
    from tests.conftest import is_resource_available

    # Test with known resource
    with patch("tests.conftest.is_lmstudio_available", return_value=True):
        assert is_resource_available("lmstudio")

    with patch("tests.conftest.is_lmstudio_available", return_value=False):
        assert not is_resource_available("lmstudio")

    # Test with unknown resource (should return True)
    assert is_resource_available("unknown_resource")


@pytest.mark.requires_resource("test_resource")
def test_with_resource_marker():
    """Test that a test with a resource marker is executed."""
    # This test should be executed because we're not checking for "test_resource"
    assert True


def test_pytest_collection_modifyitems():
    """Test that pytest_collection_modifyitems skips tests with unavailable resources."""
    from tests.conftest import pytest_collection_modifyitems

    # Create a mock item with a requires_resource marker
    class MockMarker:
        def __init__(self, name, args):
            self.name = name
            self.args = args

    class MockItem:
        def __init__(self, name, markers=None):
            self.name = name
            self._markers = markers or []
            self.user_properties = []

        def iter_markers(self, name=None):
            if name:
                return [m for m in self._markers if m.name == name]
            return self._markers

        def add_marker(self, marker):
            self._markers.append(marker)

    # Create a mock config
    class MockConfig:
        def __init__(self):
            pass

    # Create a mock item with a requires_resource marker for an unavailable resource
    item1 = MockItem(
        "test_unavailable_resource",
        [MockMarker("requires_resource", ["unavailable_resource"])],
    )

    # Create a mock item with a requires_resource marker for an available resource
    item2 = MockItem(
        "test_available_resource",
        [MockMarker("requires_resource", ["available_resource"])],
    )

    # Create a mock item without a requires_resource marker
    item3 = MockItem("test_no_resource_marker")

    items = [item1, item2, item3]

    # Mock is_resource_available to return False for "unavailable_resource" and True for "available_resource"
    with patch(
        "tests.conftest.is_resource_available", lambda r: r == "available_resource"
    ):
        # Call pytest_collection_modifyitems
        pytest_collection_modifyitems(MockConfig(), items)

    # Check that item1 has a skip marker
    skip_markers = [m for m in item1.iter_markers() if m.name == "skip"]
    assert len(skip_markers) == 1

    # Check that item2 and item3 don't have skip markers
    assert not any(m.name == "skip" for m in item2.iter_markers())
    assert not any(m.name == "skip" for m in item3.iter_markers())
