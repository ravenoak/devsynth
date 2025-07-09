import os
import pytest
from unittest.mock import patch
pytest.skip('Resource marker tests skipped', allow_module_level=True)


def test_is_lmstudio_available_succeeds():
    """Test that is_lmstudio_available obeys environment variables and HTTP checks.

ReqID: N/A"""
    with patch.dict(os.environ, {}, clear=True):
        with patch('requests.get') as mock_get:
            from tests.conftest import is_lmstudio_available
            assert not is_lmstudio_available()
            mock_get.assert_not_called()
    with patch.dict(os.environ, {'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE':
        'false'}):
        from tests.conftest import is_lmstudio_available
        assert not is_lmstudio_available()
    with patch.dict(os.environ, {'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE':
        'true'}):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            from tests.conftest import is_lmstudio_available
            assert is_lmstudio_available()
    with patch.dict(os.environ, {'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE':
        'true'}):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            from tests.conftest import is_lmstudio_available
            assert not is_lmstudio_available()
    with patch.dict(os.environ, {'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE':
        'true'}):
        with patch('requests.get', side_effect=Exception('Connection error')):
            from tests.conftest import is_lmstudio_available
            assert not is_lmstudio_available()


def test_is_codebase_available_succeeds():
    """Test that is_codebase_available checks environment variables and file existence.

ReqID: N/A"""
    with patch.dict(os.environ, {'DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE':
        'false'}):
        from tests.conftest import is_codebase_available
        assert not is_codebase_available()
    with patch('pathlib.Path.exists', return_value=True):
        from tests.conftest import is_codebase_available
        assert is_codebase_available()
    with patch('pathlib.Path.exists', return_value=False):
        from tests.conftest import is_codebase_available
        assert not is_codebase_available()


def test_is_cli_available_succeeds():
    """Test that is_cli_available checks environment variables and CLI availability.

ReqID: N/A"""
    with patch.dict(os.environ, {'DEVSYNTH_RESOURCE_CLI_AVAILABLE': 'false'}):
        from tests.conftest import is_cli_available
        assert not is_cli_available()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        from tests.conftest import is_cli_available
        assert is_cli_available()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        from tests.conftest import is_cli_available
        assert not is_cli_available()
    with patch('subprocess.run', side_effect=Exception('Command not found')):
        from tests.conftest import is_cli_available
        assert not is_cli_available()


def test_is_resource_available_succeeds():
    """Test that is_resource_available calls the correct checker function.

ReqID: N/A"""
    from tests.conftest import is_resource_available
    with patch('tests.conftest.is_lmstudio_available', return_value=True):
        assert is_resource_available('lmstudio')
    with patch('tests.conftest.is_lmstudio_available', return_value=False):
        assert not is_resource_available('lmstudio')
    assert is_resource_available('unknown_resource')


@pytest.mark.requires_resource('test_resource')
def test_with_resource_marker_succeeds():
    """Test that a test with a resource marker is executed.

ReqID: N/A"""
    assert True


def test_pytest_collection_modifyitems_succeeds():
    """Test that pytest_collection_modifyitems skips tests with unavailable resources.

ReqID: N/A"""
    from tests.conftest import pytest_collection_modifyitems


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


    class MockConfig:

        def __init__(self):
            pass
    item1 = MockItem('test_unavailable_resource', [MockMarker(
        'requires_resource', ['unavailable_resource'])])
    item2 = MockItem('test_available_resource', [MockMarker(
        'requires_resource', ['available_resource'])])
    item3 = MockItem('test_no_resource_marker')
    items = [item1, item2, item3]
    with patch('tests.conftest.is_resource_available', lambda r: r ==
        'available_resource'):
        pytest_collection_modifyitems(MockConfig(), items)
    skip_markers = [m for m in item1.iter_markers() if m.name == 'skip']
    assert len(skip_markers) == 1
    assert not any(m.name == 'skip' for m in item2.iter_markers())
    assert not any(m.name == 'skip' for m in item3.iter_markers())
