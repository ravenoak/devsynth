"""Integration tests for error handling at integration points.

This test verifies that errors are properly handled at various integration points in the system,
including between components, across boundaries, and in error recovery scenarios.
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.methodology.base import Phase
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.provider_system import (
    OpenAIProvider,
    LMStudioProvider,
    FallbackProvider,
    ProviderError
)


class TestErrorHandlingAtIntegrationPoints:
    """Test error handling at various integration points in the system."""

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
        team = WSDETeam()
        
        # Add agents with different expertise
        team.add_agent(UnifiedAgent(
            name="Explorer",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["exploration", "brainstorming"])
        ))
        team.add_agent(UnifiedAgent(
            name="Analyzer",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["analysis", "evaluation"])
        ))
        
        # Mock the team methods to avoid actual LLM calls
        team.generate_diverse_ideas = MagicMock(return_value=[
            {"id": "idea1", "content": "First idea"},
            {"id": "idea2", "content": "Second idea"}
        ])
        team.evaluate_options = MagicMock(return_value=[
            {"id": "idea1", "evaluation": {"quality": 0.8, "feasibility": 0.7}},
            {"id": "idea2", "evaluation": {"quality": 0.6, "feasibility": 0.9}}
        ])
        team.select_best_option = MagicMock(return_value={"id": "idea1", "content": "First idea"})
        
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
            config={"edrr": {"quality_based_transitions": True}}
        )

    def test_error_handling_in_edrr_wsde_integration(self, coordinator):
        """Test error handling in the EDRR-WSDE integration."""
        # Start a cycle with a task
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation"
        }
        coordinator.start_cycle(task)
        
        # Mock the WSDE team methods to raise exceptions
        coordinator.wsde_team.generate_diverse_ideas.side_effect = ValueError("Test error in generate_diverse_ideas")
        
        # Execute the EXPAND phase and verify that the error is handled
        try:
            expand_results = coordinator.execute_current_phase()
            assert False, "Expected ValueError was not raised"
        except ValueError as e:
            assert "Test error in generate_diverse_ideas" in str(e)
        
        # Reset the mock and continue with the test
        coordinator.wsde_team.generate_diverse_ideas.side_effect = None
        coordinator.wsde_team.generate_diverse_ideas.return_value = [
            {"id": "idea1", "content": "First idea"},
            {"id": "idea2", "content": "Second idea"}
        ]
        
        # Execute the EXPAND phase again
        expand_results = coordinator.execute_current_phase()
        
        # Progress to the DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Mock the WSDE team methods to raise exceptions
        coordinator.wsde_team.evaluate_options.side_effect = ValueError("Test error in evaluate_options")
        
        # Execute the DIFFERENTIATE phase and verify that the error is handled
        try:
            differentiate_results = coordinator.execute_current_phase()
            assert False, "Expected ValueError was not raised"
        except ValueError as e:
            assert "Test error in evaluate_options" in str(e)

    def test_error_handling_in_memory_integration(self, memory_manager):
        """Test error handling in the memory integration."""
        # Mock the memory adapter to raise exceptions
        memory_manager.adapters["default"].store = MagicMock(side_effect=Exception("Test error in store"))
        
        # Attempt to store a memory item and verify that the error is handled
        try:
            memory_manager.store(MemoryItem(
                id="",
                content="Test content",
                memory_type=MemoryType.KNOWLEDGE,
                metadata={"source": "test"}
            ))
            assert False, "Expected Exception was not raised"
        except Exception as e:
            assert "Test error in store" in str(e)
        
        # Reset the mock and continue with the test
        memory_manager.adapters["default"].store = MagicMock()
        
        # Store a memory item
        memory_id = memory_manager.store(MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"source": "test"}
        ))
        
        # Mock the memory adapter to raise exceptions
        memory_manager.adapters["default"].retrieve = MagicMock(side_effect=Exception("Test error in retrieve"))
        
        # Attempt to retrieve a memory item and verify that the error is handled
        try:
            memory_manager.retrieve(memory_id)
            assert False, "Expected Exception was not raised"
        except Exception as e:
            assert "Test error in retrieve" in str(e)

    def test_error_handling_in_provider_integration(self):
        """Test error handling in the provider integration."""
        # Create a provider that raises exceptions
        provider = OpenAIProvider(api_key="test_key")
        provider.complete = MagicMock(side_effect=ProviderError("Test error in complete"))
        
        # Attempt to complete a prompt and verify that the error is handled
        try:
            provider.complete("Test prompt")
            assert False, "Expected ProviderError was not raised"
        except ProviderError as e:
            assert "Test error in complete" in str(e)
        
        # Test fallback provider error handling
        provider1 = OpenAIProvider(api_key="test_key")
        provider1.complete = MagicMock(side_effect=ProviderError("Test error in provider1"))
        
        provider2 = LMStudioProvider(endpoint="http://localhost:1234")
        provider2.complete = MagicMock(side_effect=ProviderError("Test error in provider2"))
        
        fallback_provider = FallbackProvider(providers=[provider1, provider2])
        
        # Attempt to complete a prompt and verify that the error is handled
        try:
            fallback_provider.complete("Test prompt")
            assert False, "Expected ProviderError was not raised"
        except ProviderError as e:
            assert "All providers failed" in str(e)
            assert "Test error in provider1" in str(e)
            assert "Test error in provider2" in str(e)

    def test_error_handling_in_code_analysis_integration(self, coordinator):
        """Test error handling in the code analysis integration."""
        # Mock the code analyzer to raise exceptions
        coordinator.code_analyzer.analyze_code = MagicMock(side_effect=Exception("Test error in analyze_code"))
        
        # Start a cycle with a task that includes code
        task = {
            "description": "Analyze this code",
            "language": "python",
            "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"
        }
        coordinator.start_cycle(task)
        
        # Execute the EXPAND phase and verify that the error is handled
        # The EXPAND phase should still complete even if code analysis fails
        expand_results = coordinator.execute_current_phase()
        assert expand_results is not None
        
        # Mock the AST transformer to raise exceptions
        coordinator.ast_transformer.transform_code = MagicMock(side_effect=Exception("Test error in transform_code"))
        
        # Progress to the REFINE phase
        coordinator.progress_to_phase(Phase.REFINE)
        
        # Execute the REFINE phase and verify that the error is handled
        # The REFINE phase should still complete even if code transformation fails
        refine_results = coordinator.execute_current_phase()
        assert refine_results is not None

    def test_error_recovery_in_edrr_cycle(self, coordinator):
        """Test error recovery in the EDRR cycle."""
        # Start a cycle with a task
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation"
        }
        coordinator.start_cycle(task)
        
        # Mock the WSDE team methods to raise exceptions on first call but succeed on second call
        coordinator.wsde_team.generate_diverse_ideas.side_effect = [
            ValueError("Test error in generate_diverse_ideas"),
            [{"id": "idea1", "content": "First idea"}, {"id": "idea2", "content": "Second idea"}]
        ]
        
        # Execute the EXPAND phase and verify that the error is handled
        try:
            expand_results = coordinator.execute_current_phase()
            assert False, "Expected ValueError was not raised"
        except ValueError as e:
            assert "Test error in generate_diverse_ideas" in str(e)
        
        # Execute the EXPAND phase again and verify that it succeeds
        expand_results = coordinator.execute_current_phase()
        assert expand_results is not None
        
        # Progress to the DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Mock the WSDE team methods to raise exceptions on first call but succeed on second call
        coordinator.wsde_team.evaluate_options.side_effect = [
            ValueError("Test error in evaluate_options"),
            [{"id": "idea1", "evaluation": {"quality": 0.8}}, {"id": "idea2", "evaluation": {"quality": 0.6}}]
        ]
        
        # Execute the DIFFERENTIATE phase and verify that the error is handled
        try:
            differentiate_results = coordinator.execute_current_phase()
            assert False, "Expected ValueError was not raised"
        except ValueError as e:
            assert "Test error in evaluate_options" in str(e)
        
        # Execute the DIFFERENTIATE phase again and verify that it succeeds
        differentiate_results = coordinator.execute_current_phase()
        assert differentiate_results is not None

    def test_error_handling_in_cross_component_integration(self, coordinator, memory_manager):
        """Test error handling in cross-component integration."""
        # Mock the memory manager to raise exceptions
        memory_manager.store_with_edrr_phase = MagicMock(side_effect=Exception("Test error in store_with_edrr_phase"))
        
        # Start a cycle with a task
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation"
        }
        coordinator.start_cycle(task)
        
        # Execute the EXPAND phase and verify that the error is handled
        # The EXPAND phase should still complete even if memory storage fails
        expand_results = coordinator.execute_current_phase()
        assert expand_results is not None
        
        # Reset the mock and continue with the test
        memory_manager.store_with_edrr_phase = MagicMock()
        
        # Mock the memory manager to raise exceptions
        memory_manager.retrieve_with_edrr_phase = MagicMock(side_effect=Exception("Test error in retrieve_with_edrr_phase"))
        
        # Progress to the DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Execute the DIFFERENTIATE phase and verify that the error is handled
        # The DIFFERENTIATE phase should still complete even if memory retrieval fails
        differentiate_results = coordinator.execute_current_phase()
        assert differentiate_results is not None