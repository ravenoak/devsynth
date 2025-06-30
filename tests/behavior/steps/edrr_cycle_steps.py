from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, when, then, scenarios

from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd
from devsynth.methodology.base import Phase

scenarios('../features/edrr_cycle.feature')


@pytest.fixture
def context():
    return {}


@given('a valid manifest file')
def valid_manifest(tmp_path, context):
    manifest = tmp_path / 'manifest.yaml'
    manifest.write_text('project: test')
    context['manifest'] = manifest
    return manifest


@given('no manifest file exists at the provided path')
def missing_manifest(tmp_path, context):
    context['manifest'] = tmp_path / 'missing.yaml'
    return context['manifest']


@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context):
    manifest = str(context['manifest'])
    with patch('devsynth.application.cli.commands.edrr_cycle_cmd.bridge') as mock_bridge, \
         patch('devsynth.application.cli.commands.edrr_cycle_cmd.EDRRCoordinator') as coord_cls, \
         patch('devsynth.application.cli.commands.edrr_cycle_cmd.MemoryManager') as manager_cls, \
         patch('devsynth.core.config_loader.load_config') as cfg_loader:
        cfg = MagicMock()
        cfg.as_dict.return_value = {}
        cfg_loader.return_value = cfg
        coordinator = MagicMock()
        coordinator.generate_report.return_value = {'ok': True}
        coordinator.cycle_id = 'cid'
        coord_cls.return_value = coordinator

        memory_manager = MagicMock()
        memory_manager.store_with_edrr_phase.return_value = 'rid'
        manager_cls.return_value = memory_manager

        edrr_cycle_cmd(manifest)

        context['bridge'] = mock_bridge
        context['coordinator'] = coordinator
        context['memory_manager'] = memory_manager
        context['coord_cls'] = coord_cls


@then('the coordinator should process the manifest')
def coordinator_processed_manifest(context):
    context['coord_cls'].assert_called_once()
    context['coordinator'].start_cycle_from_manifest.assert_called_once_with(
        context['manifest'], is_file=True
    )
    assert context['coordinator'].progress_to_phase.call_count == 4


@then('the workflow should complete successfully')
def workflow_completed(context):
    context['memory_manager'].store_with_edrr_phase.assert_called_once_with(
        context['coordinator'].generate_report.return_value,
        'EDRR_CYCLE_RESULTS',
        Phase.RETROSPECT.value,
        {'cycle_id': context['coordinator'].cycle_id},
    )
    assert any(
        'EDRR cycle completed' in call.args[0]
        for call in context['bridge'].print.call_args_list
    )


@then('the system should report that the manifest file was not found')
def manifest_not_found_error(context):
    context['bridge'].print.assert_called_once_with(
        f"[red]Manifest file not found:[/red] {context['manifest']}"
    )
