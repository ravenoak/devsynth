"""Integration tests for WSDE and EDRR component interactions.

This test verifies the interactions between WSDE and EDRR components, focusing on
the integration points and data flow between them.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import tempfile
import shutil
import os
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


class TestWSDEEDRRComponentInteractions:
    """Test the interactions between WSDE and EDRR components."""

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
        team.add_agent(UnifiedAgent(
            name="Developer",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["implementation", "coding"])
        ))
        team.add_agent(UnifiedAgent(
            name="Reviewer",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["review", "quality assurance"])
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
        team.elaborate_details = MagicMock(return_value=[
            {"step": 1, "description": "First step"},
            {"step": 2, "description": "Second step"}
        ])
        team.create_implementation_plan = MagicMock(return_value={
            "steps": [
                {"step": 1, "description": "First step", "code": "def step1(): pass"},
                {"step": 2, "description": "Second step", "code": "def step2(): pass"}
            ]
        })
        team.optimize_implementation = MagicMock(return_value={
            "optimized_code": "def optimized(): pass"
        })
        team.perform_quality_assurance = MagicMock(return_value={
            "issues": [],
            "quality_score": 0.9
        })
        team.extract_learnings = MagicMock(return_value=[
            {"learning": "First learning"},
            {"learning": "Second learning"}
        ])
        
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

    def test_wsde_team_role_assignment_in_edrr_phases(self, coordinator):
        """Test that WSDE team roles are assigned appropriately for each EDRR phase."""
        # Start a cycle with a task
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation"
        }
        coordinator.start_cycle(task)
        
        # Verify that the Primus role is assigned to the Explorer agent in the EXPAND phase
        primus = coordinator.wsde_team.get_primus()
        assert primus is not None
        assert primus.name == "Explorer"
        
        # Progress to the DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Verify that the Primus role is assigned to the Analyzer agent in the DIFFERENTIATE phase
        primus = coordinator.wsde_team.get_primus()
        assert primus is not None
        assert primus.name == "Analyzer"
        
        # Progress to the REFINE phase
        coordinator.progress_to_phase(Phase.REFINE)
        
        # Verify that the Primus role is assigned to the Developer agent in the REFINE phase
        primus = coordinator.wsde_team.get_primus()
        assert primus is not None
        assert primus.name == "Developer"
        
        # Progress to the RETROSPECT phase
        coordinator.progress_to_phase(Phase.RETROSPECT)
        
        # Verify that the Primus role is assigned to the Reviewer agent in the RETROSPECT phase
        primus = coordinator.wsde_team.get_primus()
        assert primus is not None
        assert primus.name == "Reviewer"

    def test_wsde_method_calls_in_edrr_phases(self, coordinator):
        """Test that appropriate WSDE methods are called in each EDRR phase."""
        # Start a cycle with a task
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation"
        }
        coordinator.start_cycle(task)
        
        # Execute the EXPAND phase
        coordinator.execute_current_phase()
        
        # Verify that the appropriate WSDE methods were called in the EXPAND phase
        coordinator.wsde_team.generate_diverse_ideas.assert_called_once()
        
        # Progress to the DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Execute the DIFFERENTIATE phase
        coordinator.execute_current_phase()
        
        # Verify that the appropriate WSDE methods were called in the DIFFERENTIATE phase
        coordinator.wsde_team.evaluate_options.assert_called_once()
        coordinator.wsde_team.select_best_option.assert_called_once()
        
        # Progress to the REFINE phase
        coordinator.progress_to_phase(Phase.REFINE)
        
        # Execute the REFINE phase
        coordinator.execute_current_phase()
        
        # Verify that the appropriate WSDE methods were called in the REFINE phase
        coordinator.wsde_team.elaborate_details.assert_called_once()
        coordinator.wsde_team.create_implementation_plan.assert_called_once()
        coordinator.wsde_team.optimize_implementation.assert_called_once()
        
        # Progress to the RETROSPECT phase
        coordinator.progress_to_phase(Phase.RETROSPECT)
        
        # Execute the RETROSPECT phase
        coordinator.execute_current_phase()
        
        # Verify that the appropriate WSDE methods were called in the RETROSPECT phase
        coordinator.wsde_team.perform_quality_assurance.assert_called_once()
        coordinator.wsde_team.extract_learnings.assert_called_once()

    def test_memory_integration_in_edrr_wsde_workflow(self, coordinator, memory_manager):
        """Test that memory is properly integrated in the EDRR-WSDE workflow."""
        # Mock the memory manager methods to track calls
        memory_manager.store_with_edrr_phase = MagicMock(wraps=memory_manager.store_with_edrr_phase)
        memory_manager.retrieve_with_edrr_phase = MagicMock(wraps=memory_manager.retrieve_with_edrr_phase)
        
        # Start a cycle with a task
        task = {
            "description": "Create a Python function to calculate factorial",
            "language": "python",
            "domain": "code_generation"
        }
        coordinator.start_cycle(task)
        
        # Execute the EXPAND phase
        expand_results = coordinator.execute_current_phase()
        
        # Verify that the results were stored in memory
        memory_manager.store_with_edrr_phase.assert_called()
        
        # Progress to the DIFFERENTIATE phase
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)
        
        # Verify that the previous phase results are retrieved from memory
        memory_manager.retrieve_with_edrr_phase.assert_called()
        
        # Execute the DIFFERENTIATE phase
        differentiate_results = coordinator.execute_current_phase()
        
        # Verify that the results were stored in memory
        assert memory_manager.store_with_edrr_phase.call_count >= 2
        
        # Progress to the REFINE phase
        coordinator.progress_to_phase(Phase.REFINE)
        
        # Verify that the previous phase results are retrieved from memory
        assert memory_manager.retrieve_with_edrr_phase.call_count >= 2
        
        # Execute the REFINE phase
        refine_results = coordinator.execute_current_phase()
        
        # Verify that the results were stored in memory
        assert memory_manager.store_with_edrr_phase.call_count >= 3
        
        # Progress to the RETROSPECT phase
        coordinator.progress_to_phase(Phase.RETROSPECT)
        
        # Verify that the previous phase results are retrieved from memory
        assert memory_manager.retrieve_with_edrr_phase.call_count >= 3
        
        # Execute the RETROSPECT phase
        retrospect_results = coordinator.execute_current_phase()
        
        # Verify that the results were stored in memory
        assert memory_manager.store_with_edrr_phase.call_count >= 4
        
        # Generate the final report
        report = coordinator.generate_report()
        
        # Verify that the report was generated and includes all phases
        assert report is not None
        assert "cycle_id" in report
        assert "phases" in report
        assert len(report["phases"]) == 4
        assert Phase.EXPAND.name in report["phases"]
        assert Phase.DIFFERENTIATE.name in report["phases"]
        assert Phase.REFINE.name in report["phases"]
        assert Phase.RETROSPECT.name in report["phases"]

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