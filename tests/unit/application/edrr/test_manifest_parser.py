"""
Unit tests for the ManifestParser class.

This module contains tests for the ManifestParser class, which is responsible for
parsing, validating, and managing EDRR manifests.
"""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
from devsynth.application.edrr.manifest_parser import ManifestParser, ManifestParseError, MANIFEST_SCHEMA
from devsynth.methodology.base import Phase

@pytest.fixture
def valid_manifest():
    """Fixture that provides a valid EDRR manifest."""
    return {'id': 'test-manifest', 'description': 'Test manifest for unit tests', 'metadata': {'version': '1.0', 'author': 'Test Author'}, 'phases': {'expand': {'instructions': 'Expand phase instructions', 'templates': ['template1', 'template2'], 'resources': ['resource1', 'resource2']}, 'differentiate': {'instructions': 'Differentiate phase instructions', 'templates': ['template3'], 'resources': ['resource3']}, 'refine': {'instructions': 'Refine phase instructions', 'templates': ['template4'], 'resources': ['resource4']}, 'retrospect': {'instructions': 'Retrospect phase instructions', 'templates': ['template5'], 'resources': ['resource5']}}}

@pytest.fixture
def manifest_parser():
    """Fixture that provides a ManifestParser instance."""
    return ManifestParser()

@pytest.fixture
def manifest_parser_with_manifest(manifest_parser, valid_manifest):
    """Fixture that provides a ManifestParser instance with a loaded manifest."""
    manifest_parser.manifest = valid_manifest
    return manifest_parser

@pytest.fixture
def manifest_file(valid_manifest):
    """Fixture that provides a temporary file with a valid EDRR manifest."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_manifest, f)
        temp_file_path = f.name
    yield temp_file_path
    Path(temp_file_path).unlink(missing_ok=True)

class TestManifestParser:
    """Tests for the ManifestParser class.

ReqID: N/A"""

    @pytest.mark.medium
    def test_init_succeeds(self):
        """Test that the ManifestParser initializes correctly.

ReqID: N/A"""
        parser = ManifestParser()
        assert parser.manifest is None
        assert parser.execution_trace == {}
        assert parser.phase_dependencies == {Phase.DIFFERENTIATE: {Phase.EXPAND}, Phase.REFINE: {Phase.DIFFERENTIATE}, Phase.RETROSPECT: {Phase.REFINE}}
        assert parser.phase_status == {}
        assert parser.start_time is None

    @pytest.mark.medium
    def test_parse_file_valid_is_valid(self, manifest_parser, manifest_file):
        """Test parsing a valid manifest file.

ReqID: N/A"""
        manifest = manifest_parser.parse_file(manifest_file)
        assert manifest['id'] == 'test-manifest'
        assert manifest['description'] == 'Test manifest for unit tests'
        assert manifest['phases']['expand']['instructions'] == 'Expand phase instructions'
        assert manifest_parser.manifest == manifest

    @pytest.mark.medium
    def test_parse_file_invalid_json_is_valid(self, manifest_parser):
        """Test parsing an invalid JSON file.

ReqID: N/A"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('This is not valid JSON')
            temp_file_path = f.name
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.parse_file(temp_file_path)
        assert 'Failed to parse EDRR manifest from file' in str(excinfo.value)
        Path(temp_file_path).unlink(missing_ok=True)

    @pytest.mark.medium
    def test_parse_file_not_found_succeeds(self, manifest_parser):
        """Test parsing a file that doesn't exist.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.parse_file('nonexistent_file.json')
        assert 'Failed to parse EDRR manifest from file' in str(excinfo.value)

    @pytest.mark.medium
    def test_parse_string_valid_is_valid(self, manifest_parser, valid_manifest):
        """Test parsing a valid manifest string.

ReqID: N/A"""
        manifest_str = json.dumps(valid_manifest)
        manifest = manifest_parser.parse_string(manifest_str)
        assert manifest['id'] == 'test-manifest'
        assert manifest['description'] == 'Test manifest for unit tests'
        assert manifest['phases']['expand']['instructions'] == 'Expand phase instructions'
        assert manifest_parser.manifest == manifest

    @pytest.mark.medium
    def test_parse_string_invalid_json_is_valid(self, manifest_parser):
        """Test parsing an invalid JSON string.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.parse_string('This is not valid JSON')
        assert 'Failed to parse EDRR manifest from string' in str(excinfo.value)

    @pytest.mark.medium
    @patch('jsonschema.validate')
    def test_validate_valid_is_valid(self, mock_validate, manifest_parser, valid_manifest):
        """Test validating a valid manifest.

ReqID: N/A"""
        manifest_parser.validate(valid_manifest)
        mock_validate.assert_called_once_with(instance=valid_manifest, schema=MANIFEST_SCHEMA)

    @pytest.mark.medium
    @patch('jsonschema.validate')
    def test_validate_invalid_is_valid(self, mock_validate, manifest_parser):
        """Test validating an invalid manifest.

ReqID: N/A"""
        mock_validate.side_effect = Exception('Invalid manifest')
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.validate({})
        assert 'Invalid EDRR manifest' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_instructions_has_expected(self, manifest_parser_with_manifest):
        """Test getting phase instructions.

ReqID: N/A"""
        instructions = manifest_parser_with_manifest.get_phase_instructions(Phase.EXPAND)
        assert instructions == 'Expand phase instructions'

    @pytest.mark.medium
    def test_get_phase_instructions_no_manifest_has_expected(self, manifest_parser):
        """Test getting phase instructions with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_phase_instructions(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_instructions_phase_not_found_has_expected(self, manifest_parser_with_manifest):
        """Test getting instructions for a phase that doesn't exist in the manifest.

ReqID: N/A"""
        mock_phase = MagicMock()
        mock_phase.value.lower.return_value = 'custom'
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser_with_manifest.get_phase_instructions(mock_phase)
        assert "Phase 'custom' not found in manifest" in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_templates_has_expected(self, manifest_parser_with_manifest):
        """Test getting phase templates.

ReqID: N/A"""
        templates = manifest_parser_with_manifest.get_phase_templates(Phase.EXPAND)
        assert templates == ['template1', 'template2']

    @pytest.mark.medium
    def test_get_phase_templates_no_manifest_has_expected(self, manifest_parser):
        """Test getting phase templates with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_phase_templates(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_templates_phase_not_found_has_expected(self, manifest_parser_with_manifest):
        """Test getting templates for a phase that doesn't exist in the manifest.

ReqID: N/A"""
        mock_phase = MagicMock()
        mock_phase.value.lower.return_value = 'custom'
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser_with_manifest.get_phase_templates(mock_phase)
        assert "Phase 'custom' not found in manifest" in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_resources_has_expected(self, manifest_parser_with_manifest):
        """Test getting phase resources.

ReqID: N/A"""
        resources = manifest_parser_with_manifest.get_phase_resources(Phase.EXPAND)
        assert resources == ['resource1', 'resource2']

    @pytest.mark.medium
    def test_get_phase_resources_no_manifest_has_expected(self, manifest_parser):
        """Test getting phase resources with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_phase_resources(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_resources_phase_not_found_has_expected(self, manifest_parser_with_manifest):
        """Test getting resources for a phase that doesn't exist in the manifest.

ReqID: N/A"""
        mock_phase = MagicMock()
        mock_phase.value.lower.return_value = 'custom'
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser_with_manifest.get_phase_resources(mock_phase)
        assert "Phase 'custom' not found in manifest" in str(excinfo.value)

    @pytest.mark.medium
    def test_get_manifest_id_succeeds(self, manifest_parser_with_manifest):
        """Test getting the manifest ID.

ReqID: N/A"""
        manifest_id = manifest_parser_with_manifest.get_manifest_id()
        assert manifest_id == 'test-manifest'

    @pytest.mark.medium
    def test_get_manifest_id_no_manifest_succeeds(self, manifest_parser):
        """Test getting the manifest ID with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_manifest_id()
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_manifest_description_succeeds(self, manifest_parser_with_manifest):
        """Test getting the manifest description.

ReqID: N/A"""
        description = manifest_parser_with_manifest.get_manifest_description()
        assert description == 'Test manifest for unit tests'

    @pytest.mark.medium
    def test_get_manifest_description_no_manifest_succeeds(self, manifest_parser):
        """Test getting the manifest description with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_manifest_description()
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_manifest_metadata_succeeds(self, manifest_parser_with_manifest):
        """Test getting the manifest metadata.

ReqID: N/A"""
        metadata = manifest_parser_with_manifest.get_manifest_metadata()
        assert metadata == {'version': '1.0', 'author': 'Test Author'}

    @pytest.mark.medium
    def test_get_manifest_metadata_no_manifest_succeeds(self, manifest_parser):
        """Test getting the manifest metadata with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_manifest_metadata()
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_manifest_metadata_no_metadata_succeeds(self, manifest_parser_with_manifest):
        """Test getting the manifest metadata when none is specified.

ReqID: N/A"""
        manifest_parser_with_manifest.manifest.pop('metadata')
        metadata = manifest_parser_with_manifest.get_manifest_metadata()
        assert metadata == {}

    @pytest.mark.medium
    def test_start_execution_succeeds(self, manifest_parser_with_manifest):
        """Test starting execution tracking.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        assert manifest_parser_with_manifest.start_time is not None
        assert manifest_parser_with_manifest.execution_trace['manifest_id'] == 'test-manifest'
        assert 'start_time' in manifest_parser_with_manifest.execution_trace
        assert manifest_parser_with_manifest.execution_trace['completed'] is False
        assert 'phases' in manifest_parser_with_manifest.execution_trace
        for phase in Phase:
            assert phase in manifest_parser_with_manifest.phase_status
            assert manifest_parser_with_manifest.phase_status[phase]['status'] == 'pending'
            assert manifest_parser_with_manifest.phase_status[phase]['start_time'] is None
            assert manifest_parser_with_manifest.phase_status[phase]['end_time'] is None
            assert manifest_parser_with_manifest.phase_status[phase]['duration'] is None
            if phase not in manifest_parser_with_manifest.phase_dependencies:
                assert manifest_parser_with_manifest.phase_status[phase]['dependencies_met'] is True
            else:
                assert manifest_parser_with_manifest.phase_status[phase]['dependencies_met'] is False

    @pytest.mark.medium
    def test_start_execution_no_manifest_succeeds(self, manifest_parser):
        """Test starting execution tracking with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.start_execution()
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_check_phase_dependencies_has_expected(self, manifest_parser_with_manifest):
        """Test checking phase dependencies.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        assert manifest_parser_with_manifest.check_phase_dependencies(Phase.EXPAND) is True
        assert manifest_parser_with_manifest.check_phase_dependencies(Phase.DIFFERENTIATE) is False
        manifest_parser_with_manifest.phase_status[Phase.EXPAND]['status'] = 'completed'
        assert manifest_parser_with_manifest.check_phase_dependencies(Phase.DIFFERENTIATE) is True

    @pytest.mark.medium
    def test_check_phase_dependencies_no_manifest_has_expected(self, manifest_parser):
        """Test checking phase dependencies with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.check_phase_dependencies(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_start_phase_has_expected(self, manifest_parser_with_manifest):
        """Test starting phase tracking.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        manifest_parser_with_manifest.start_phase(Phase.EXPAND)
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['status'] == 'in_progress'
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['start_time'] is not None
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['dependencies_met'] is True
        assert manifest_parser_with_manifest.execution_trace['phases']['expand']['status'] == 'in_progress'
        assert manifest_parser_with_manifest.execution_trace['phases']['expand']['start_time'] is not None

    @pytest.mark.medium
    def test_start_phase_no_manifest_has_expected(self, manifest_parser):
        """Test starting phase tracking with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.start_phase(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_start_phase_dependencies_not_met_has_expected(self, manifest_parser_with_manifest):
        """Test starting a phase with unmet dependencies.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser_with_manifest.start_phase(Phase.DIFFERENTIATE)
        assert 'Dependencies not met for phase' in str(excinfo.value)

    @pytest.mark.medium
    def test_complete_phase_has_expected(self, manifest_parser_with_manifest):
        """Test completing phase tracking.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        manifest_parser_with_manifest.start_phase(Phase.EXPAND)
        result = {'output': 'Expand phase output'}
        manifest_parser_with_manifest.complete_phase(Phase.EXPAND, result)
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['status'] == 'completed'
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['end_time'] is not None
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['duration'] is not None
        assert manifest_parser_with_manifest.phase_status[Phase.EXPAND]['result'] == result
        assert manifest_parser_with_manifest.execution_trace['phases']['expand']['status'] == 'completed'
        assert manifest_parser_with_manifest.execution_trace['phases']['expand']['end_time'] is not None
        assert manifest_parser_with_manifest.execution_trace['phases']['expand']['duration'] is not None
        assert manifest_parser_with_manifest.execution_trace['phases']['expand']['result'] == result
        assert manifest_parser_with_manifest.phase_status[Phase.DIFFERENTIATE]['dependencies_met'] is True

    @pytest.mark.medium
    def test_complete_phase_no_manifest_has_expected(self, manifest_parser):
        """Test completing phase tracking with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.complete_phase(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_complete_phase_not_in_progress_has_expected(self, manifest_parser_with_manifest):
        """Test completing a phase that is not in progress.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser_with_manifest.complete_phase(Phase.EXPAND)
        assert 'is not in progress' in str(excinfo.value)

    @pytest.mark.medium
    def test_complete_execution_succeeds(self, manifest_parser_with_manifest):
        """Test completing execution tracking.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        manifest_parser_with_manifest.start_phase(Phase.EXPAND)
        manifest_parser_with_manifest.complete_phase(Phase.EXPAND)
        manifest_parser_with_manifest.start_phase(Phase.DIFFERENTIATE)
        manifest_parser_with_manifest.complete_phase(Phase.DIFFERENTIATE)
        manifest_parser_with_manifest.start_phase(Phase.REFINE)
        manifest_parser_with_manifest.complete_phase(Phase.REFINE)
        manifest_parser_with_manifest.start_phase(Phase.RETROSPECT)
        manifest_parser_with_manifest.complete_phase(Phase.RETROSPECT)
        trace = manifest_parser_with_manifest.complete_execution()
        assert trace['end_time'] is not None
        assert trace['duration'] is not None
        assert trace['completed'] is True

    @pytest.mark.medium
    def test_complete_execution_no_manifest_succeeds(self, manifest_parser):
        """Test completing execution tracking with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.complete_execution()
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_complete_execution_not_all_phases_completed_has_expected(self, manifest_parser_with_manifest):
        """Test completing execution when not all phases are completed.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        manifest_parser_with_manifest.start_phase(Phase.EXPAND)
        manifest_parser_with_manifest.complete_phase(Phase.EXPAND)
        trace = manifest_parser_with_manifest.complete_execution()
        assert trace['end_time'] is not None
        assert trace['duration'] is not None
        assert trace['completed'] is False

    @pytest.mark.medium
    def test_get_execution_trace_succeeds(self, manifest_parser_with_manifest):
        """Test getting the execution trace.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        trace = manifest_parser_with_manifest.get_execution_trace()
        assert trace['manifest_id'] == 'test-manifest'
        assert 'start_time' in trace
        assert trace['completed'] is False
        assert 'phases' in trace

    @pytest.mark.medium
    def test_get_execution_trace_no_manifest_succeeds(self, manifest_parser):
        """Test getting the execution trace with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_execution_trace()
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_status_has_expected(self, manifest_parser_with_manifest):
        """Test getting the phase status.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        status = manifest_parser_with_manifest.get_phase_status(Phase.EXPAND)
        assert status['status'] == 'pending'
        assert status['start_time'] is None
        assert status['end_time'] is None
        assert status['duration'] is None
        assert status['dependencies_met'] is True

    @pytest.mark.medium
    def test_get_phase_status_no_manifest_has_expected(self, manifest_parser):
        """Test getting the phase status with no manifest loaded.

ReqID: N/A"""
        with pytest.raises(ManifestParseError) as excinfo:
            manifest_parser.get_phase_status(Phase.EXPAND)
        assert 'No manifest loaded' in str(excinfo.value)

    @pytest.mark.medium
    def test_get_phase_status_unknown_phase_has_expected(self, manifest_parser_with_manifest):
        """Test getting the status of an unknown phase.

ReqID: N/A"""
        manifest_parser_with_manifest.start_execution()
        mock_phase = MagicMock()
        mock_phase.value.lower.return_value = 'custom'
        status = manifest_parser_with_manifest.get_phase_status(mock_phase)
        assert status == {}