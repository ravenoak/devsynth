"""Integration tests for error handling at integration points.

This test verifies that errors are properly handled at various integration points in the system,
including between components, across boundaries, and in error recovery scenarios.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

pytest.importorskip("lmstudio")
if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
    pytest.skip("LMStudio service not available", allow_module_level=True)

from devsynth.adapters.provider_system import FallbackProvider
from devsynth.adapters.provider_system import LMStudioProvider as PS_LMStudioProvider
from devsynth.adapters.provider_system import OpenAIProvider, ProviderError
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinatorError
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.llm.providers import LMStudioProvider
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase

pytestmark = [pytest.mark.requires_resource("lmstudio")]


class TestErrorHandlingAtIntegrationPoints:
    """Test error handling at various integration points in the system.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_adapter(self, temp_dir):
        """Create a memory adapter for testing."""
        db_path = os.path.join(temp_dir, "memory.json")
        return TinyDBMemoryAdapter(db_path=db_path)

    @pytest.fixture
    def memory_manager(self, memory_adapter):
        """Create a memory manager for testing."""
        return MemoryManager(adapters={"default": memory_adapter})

    @pytest.fixture
    def wsde_team(self):
        """Create a WSDE team with mock agents for testing."""
        team = WSDETeam(name="TestErrorHandlingAtIntegrationPointsTeam")
        explorer = UnifiedAgent()
        explorer.initialize(
            AgentConfig(
                name="Explorer",
                agent_type=AgentType.ORCHESTRATOR,
                description="Explorer agent",
                capabilities=["exploration", "brainstorming"],
            )
        )
        team.add_agent(explorer)

        analyzer = UnifiedAgent()
        analyzer.initialize(
            AgentConfig(
                name="Analyzer",
                agent_type=AgentType.ORCHESTRATOR,
                description="Analyzer agent",
                capabilities=["analysis", "evaluation"],
            )
        )
        team.add_agent(analyzer)
        team.generate_diverse_ideas = MagicMock(
            return_value=[
                {"id": "idea1", "content": "First idea"},
                {"id": "idea2", "content": "Second idea"},
            ]
        )
        team.evaluate_options = MagicMock(
            return_value=[
                {"id": "idea1", "evaluation": {"quality": 0.8, "feasibility": 0.7}},
                {"id": "idea2", "evaluation": {"quality": 0.6, "feasibility": 0.9}},
            ]
        )
        team.select_best_option = MagicMock(
            return_value={"id": "idea1", "content": "First idea"}
        )
        return team

    @pytest.fixture
    def coordinator(self, memory_manager, wsde_team):
        """Create an EDRR coordinator for testing."""
        return EnhancedEDRRCoordinator(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=MagicMock(spec=CodeAnalyzer),
            ast_transformer=MagicMock(spec=AstTransformer),
            prompt_manager=MagicMock(spec=PromptManager),
            documentation_manager=MagicMock(spec=DocumentationManager),
            config={"edrr": {"quality_based_transitions": True}},
        )

    @pytest.mark.medium
    def test_error_handling_in_edrr_wsde_integration_raises_error(self, coordinator):
        """Test error handling in the EDRR-WSDE integration.

        ReqID: N/A"""
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation",
        }
        coordinator.start_cycle(task)
        coordinator.wsde_team.generate_diverse_ideas.side_effect = ValueError(
            "Test error in generate_diverse_ideas"
        )
        try:
            expand_results = coordinator.execute_current_phase()
            assert False, "Expected EDRRCoordinatorError was not raised"
        except EDRRCoordinatorError as e:
            assert "Test error in generate_diverse_ideas" in str(e)
        coordinator.wsde_team.generate_diverse_ideas.side_effect = None
        coordinator.wsde_team.generate_diverse_ideas.return_value = [
            {"id": "idea1", "content": "First idea"},
            {"id": "idea2", "content": "Second idea"},
        ]
        expand_results = coordinator.execute_current_phase()
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        coordinator.wsde_team.evaluate_options.side_effect = ValueError(
            "Test error in evaluate_options"
        )
        try:
            differentiate_results = coordinator.execute_current_phase()
            assert False, "Expected EDRRCoordinatorError was not raised"
        except EDRRCoordinatorError as e:
            assert "Test error in evaluate_options" in str(e)

    @pytest.mark.medium
    def test_error_handling_in_memory_integration_raises_error(self, memory_manager):
        """Test error handling in the memory integration.

        ReqID: N/A"""
        memory_manager.adapters["default"].store = MagicMock(
            side_effect=Exception("Test error in store")
        )
        try:
            memory_manager.store(
                MemoryItem(
                    id="",
                    content="Test content",
                    memory_type=MemoryType.KNOWLEDGE,
                    metadata={"source": "test"},
                )
            )
            assert False, "Expected Exception was not raised"
        except Exception as e:
            assert "Test error in store" in str(e)
        memory_manager.adapters["default"].store = MagicMock()
        memory_id = memory_manager.store(
            MemoryItem(
                id="",
                content="Test content",
                memory_type=MemoryType.KNOWLEDGE,
                metadata={"source": "test"},
            )
        )
        memory_manager.adapters["default"].retrieve = MagicMock(
            side_effect=Exception("Test error in retrieve")
        )
        try:
            memory_manager.retrieve(memory_id)
            assert False, "Expected Exception was not raised"
        except Exception as e:
            assert "Test error in retrieve" in str(e)

    @pytest.mark.medium
    def test_error_handling_in_provider_integration_raises_error(self):
        """Test error handling in the provider integration.

        ReqID: N/A"""
        provider = OpenAIProvider(api_key="test_key")
        provider.complete = MagicMock(
            side_effect=ProviderError("Test error in complete")
        )
        try:
            provider.complete("Test prompt")
            assert False, "Expected ProviderError was not raised"
        except ProviderError as e:
            assert "Test error in complete" in str(e)
        provider1 = OpenAIProvider(api_key="test_key")
        provider1.complete = MagicMock(
            side_effect=ProviderError("Test error in provider1")
        )
        provider2 = PS_LMStudioProvider(endpoint="http://localhost:1234")
        provider2.complete = MagicMock(
            side_effect=ProviderError("Test error in provider2")
        )
        fallback_provider = FallbackProvider(providers=[provider1, provider2])
        try:
            fallback_provider.complete("Test prompt")
            assert False, "Expected ProviderError was not raised"
        except ProviderError as e:
            assert "All providers failed" in str(e)
            assert "Test error in provider2" in str(e)

    @pytest.mark.medium
    def test_error_handling_in_code_analysis_integration_raises_error(
        self, coordinator
    ):
        """Test error handling in the code analysis integration.

        ReqID: N/A"""
        coordinator.code_analyzer.analyze_code = MagicMock(
            side_effect=Exception("Test error in analyze_code")
        )
        task = {
            "description": "Analyze this code",
            "language": "python",
            "code": """def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)""",
        }
        coordinator.start_cycle(task)
        expand_results = coordinator.execute_current_phase()
        assert expand_results is not None
        coordinator.ast_transformer.transform_code = MagicMock(
            side_effect=Exception("Test error in transform_code")
        )
        coordinator.progress_to_phase(Phase.REFINE)
        refine_results = coordinator.execute_current_phase()
        assert refine_results is not None

    @pytest.mark.medium
    def test_error_recovery_in_edrr_cycle_raises_error(self, coordinator):
        """Test error recovery in the EDRR cycle.

        ReqID: N/A"""
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation",
        }
        coordinator.start_cycle(task)
        coordinator.wsde_team.generate_diverse_ideas.side_effect = [
            ValueError("Test error in generate_diverse_ideas"),
            [
                {"id": "idea1", "content": "First idea"},
                {"id": "idea2", "content": "Second idea"},
            ],
        ]
        try:
            expand_results = coordinator.execute_current_phase()
            assert False, "Expected EDRRCoordinatorError was not raised"
        except EDRRCoordinatorError as e:
            assert "Test error in generate_diverse_ideas" in str(e)
        expand_results = coordinator.execute_current_phase()
        assert expand_results is not None
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        coordinator.wsde_team.evaluate_options.side_effect = [
            ValueError("Test error in evaluate_options"),
            [
                {"id": "idea1", "evaluation": {"quality": 0.8}},
                {"id": "idea2", "evaluation": {"quality": 0.6}},
            ],
        ]
        try:
            differentiate_results = coordinator.execute_current_phase()
            assert False, "Expected EDRRCoordinatorError was not raised"
        except EDRRCoordinatorError as e:
            assert "Test error in evaluate_options" in str(e)
        differentiate_results = coordinator.execute_current_phase()
        assert differentiate_results is not None

    @pytest.mark.medium
    def test_error_handling_in_cross_component_integration_raises_error(
        self, coordinator, memory_manager
    ):
        """Test error handling in cross-component integration.

        ReqID: N/A"""
        memory_manager.store_with_edrr_phase = MagicMock(
            side_effect=Exception("Test error in store_with_edrr_phase")
        )
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation",
        }
        coordinator.start_cycle(task)
        expand_results = coordinator.execute_current_phase()
        assert expand_results is not None
        memory_manager.store_with_edrr_phase = MagicMock()
        memory_manager.retrieve_with_edrr_phase = MagicMock(
            side_effect=Exception("Test error in retrieve_with_edrr_phase")
        )
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        differentiate_results = coordinator.execute_current_phase()
        assert differentiate_results is not None
