import json
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase

pytestmark = [pytest.mark.fast]


def make_coordinator():
    return EDRRCoordinator(
        memory_manager=MagicMock(spec=MemoryManager),
        wsde_team=MagicMock(spec=WSDETeam),
        code_analyzer=MagicMock(spec=CodeAnalyzer),
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=True,
    )


def test_start_cycle_from_manifest_string_succeeds():
    """Test that start cycle from manifest string succeeds.

    ReqID: N/A"""
    coord = make_coordinator()
    manifest = {"id": "m1", "description": "demo", "phases": {}}
    parser = MagicMock()
    parser.parse_string.return_value = manifest
    parser.get_manifest_id.return_value = "m1"
    parser.get_manifest_description.return_value = "demo"
    parser.get_manifest_metadata.return_value = {}
    parser.execution_trace = {"start_time": "now"}
    parser.start_execution.return_value = None
    coord.manifest_parser = parser
    with patch.object(coord, "progress_to_phase") as prog:
        coord.start_cycle_from_manifest(json.dumps(manifest), is_file=False)
    parser.parse_string.assert_called_once()
    prog.assert_called_once_with(Phase.EXPAND)
    assert coord.task["id"] == "m1"
    assert coord.manifest == manifest
