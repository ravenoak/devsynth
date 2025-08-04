import yaml
from unittest.mock import MagicMock
import pytest
# These tests previously required the DEVSYNTH_RUN_INGEST_TESTS environment
# variable to be set.  They now run unconditionally under the isolated test
# environment provided by ``global_test_isolation`` in ``tests/conftest.py``.
from devsynth.application.ingestion import Ingestion
from devsynth.methodology.base import Phase


@pytest.fixture(autouse=True)
def _non_interactive(monkeypatch):
    monkeypatch.setenv('DEVSYNTH_NONINTERACTIVE', '1')

def test_run_ingestion_invokes_edrr_phases_succeeds(tmp_path):
    """Test that run ingestion invokes edrr phases succeeds.

ReqID: N/A"""
    project_root = tmp_path
    project_root.mkdir(exist_ok=True)
    manifest = project_root / 'manifest.yaml'
    with open(manifest, 'w') as f:
        yaml.dump({'metadata': {'name': 'test'}, 'structure': {'type':
            'single_package'}}, f)
    mock_coordinator = MagicMock()
    ingestion = Ingestion(project_root, manifest, edrr_coordinator=
        mock_coordinator)
    ingestion._run_expand_phase = MagicMock()
    ingestion._run_differentiate_phase = MagicMock()
    ingestion._run_refine_phase = MagicMock()
    ingestion._run_retrospect_phase = MagicMock()
    ingestion.run_ingestion()
    mock_coordinator.start_cycle_from_manifest.assert_called_once_with(manifest
        , is_file=True)
    expected_calls = [
        (Phase.EXPAND,),
        (Phase.DIFFERENTIATE,),
        (Phase.REFINE,),
        (Phase.RETROSPECT,),
    ]
    assert [c.args for c in mock_coordinator.progress_to_phase.call_args_list] == expected_calls
