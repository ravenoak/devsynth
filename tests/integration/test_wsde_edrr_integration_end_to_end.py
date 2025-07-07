"""
End-to-end integration test for WSDE-EDRR integration.

This test verifies the complete integration between the WSDE agent model and the EDRR framework,
including dynamic role assignment, multi-agent collaboration, and dialectical reasoning.
"""
import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.methodology.base import Phase
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.application.agents.unified_agent import UnifiedAgent


class ExpertAgent(UnifiedAgent):
    """Agent with specific expertise for testing."""
    
    def __init__(self, name, expertise):
        super().__init__()
        self.name = name
        self.expertise = expertise
        self.current_role = None
        self.previous_role = None
        self.has_been_primus = False
        
        # Initialize with config
        config = AgentConfig(
            name=name,
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with expertise in {', '.join(expertise)}",
            capabilities=[],
            parameters={"expertise": expertise}
        )
        self.initialize(config)
    
    def process(self, task):
        """Process a task based on agent's expertise."""
        # For testing, return a result that includes the agent's name and expertise
        return {
            "result": f"Solution from {self.name}",
            "confidence": 0.9,
            "reasoning": f"Based on my expertise in {', '.join(self.expertise)}"
        }


@pytest.fixture
def coordinator():
    """Create an EnhancedEDRRCoordinator with a team of agents with different expertise."""
    # Create a team with agents having different expertise
    team = WSDETeam()
    team.add_agents([
        ExpertAgent("expand_agent", ["brainstorming", "exploration", "creativity", "ideation"]),
        ExpertAgent("diff_agent", ["comparison", "analysis", "evaluation", "critical thinking"]),
        ExpertAgent("refine_agent", ["implementation", "coding", "development", "optimization"]),
        ExpertAgent("retro_agent", ["evaluation", "reflection", "learning", "improvement"])
    ])
    
    # Mock the memory manager and other components
    mm = MagicMock(spec=MemoryManager)
    mm.retrieve_with_edrr_phase.return_value = []
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    mm.store_with_edrr_phase.return_value = "memory_id"
    
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    
    # Create the coordinator with enhanced features
    return EnhancedEDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        config={"edrr": {"quality_based_transitions": True, "phase_transition": {"auto": True}}}
    )


def test_wsde_edrr_integration_end_to_end(coordinator):
    """Test the complete integration between WSDE and EDRR."""
    # Start a cycle with a task
    task = {
        "description": "Create a Python function to calculate Fibonacci numbers",
        "language": "python",
        "domain": "code_generation"
    }
    coordinator.start_cycle(task)
    
    # Verify that the cycle was started
    assert coordinator.current_phase == Phase.EXPAND
    
    # Verify that the Primus role was assigned to the agent with the most relevant expertise
    primus = coordinator.wsde_team.get_primus()
    assert primus is not None
    assert "exploration" in primus.expertise or "brainstorming" in primus.expertise
    
    # Progress through all phases and verify role assignments
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        # Progress to the next phase
        coordinator.progress_to_phase(phase)
        
        # Verify that the current phase was updated
        assert coordinator.current_phase == phase
        
        # Verify that the Primus role was reassigned based on the phase
        primus = coordinator.wsde_team.get_primus()
        assert primus is not None
        
        # Verify that the Primus has relevant expertise for the current phase
        if phase == Phase.DIFFERENTIATE:
            assert any(skill in ["comparison", "analysis", "evaluation"] for skill in primus.expertise)
        elif phase == Phase.REFINE:
            assert any(skill in ["implementation", "coding", "development"] for skill in primus.expertise)
        elif phase == Phase.RETROSPECT:
            assert any(skill in ["evaluation", "reflection", "learning"] for skill in primus.expertise)
        
        # Execute the current phase
        results = coordinator.execute_current_phase()
        
        # Verify that the phase was executed successfully
        assert results is not None
    
    # Generate the final report
    report = coordinator.generate_report()
    
    # Verify that the report was generated
    assert report is not None
    assert "cycle_id" in report
    assert "phases" in report


def test_multi_agent_collaboration_with_memory(coordinator):
    """Test multi-agent collaboration with memory system."""
    # Start a cycle with a task
    task = {
        "description": "Design a user authentication system",
        "components": ["design", "security", "database"],
        "domain": "system_design"
    }
    coordinator.start_cycle(task)
    
    # Mock the build_consensus method to simulate collaboration
    original_build_consensus = coordinator.wsde_team.build_consensus
    coordinator.wsde_team.build_consensus = MagicMock(return_value={
        "consensus": "Consensus solution for user authentication",
        "contributors": [agent.name for agent in coordinator.wsde_team.agents],
        "method": "consensus_synthesis",
        "reasoning": "Combined expertise from all agents"
    })
    
    # Execute the EXPAND phase
    expand_results = coordinator.execute_current_phase()
    
    # Verify that build_consensus was called
    coordinator.wsde_team.build_consensus.assert_called()
    
    # Verify that the results were stored in memory
    coordinator.memory_manager.store_with_edrr_phase.assert_called()
    
    # Restore the original build_consensus method
    coordinator.wsde_team.build_consensus = original_build_consensus
    
    # Progress to the DIFFERENTIATE phase
    coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    
    # Verify that the previous phase results are retrieved from memory
    coordinator.memory_manager.retrieve_with_edrr_phase.assert_called()


def test_dialectical_reasoning_in_full_workflow(coordinator):
    """Test dialectical reasoning in a full workflow."""
    # Start a cycle with a task
    task = {
        "description": "Implement a secure password hashing function",
        "language": "python",
        "domain": "security"
    }
    coordinator.start_cycle(task)
    
    # Mock the apply_enhanced_dialectical_reasoning method
    original_dialectical = coordinator.wsde_team.apply_enhanced_dialectical_reasoning
    coordinator.wsde_team.apply_enhanced_dialectical_reasoning = MagicMock(return_value={
        "thesis": {"content": "Initial solution for password hashing"},
        "antithesis": {
            "critique": ["Not using a salt", "Using MD5 which is insecure"],
            "severity": "high"
        },
        "synthesis": {
            "content": "Improved solution using bcrypt with salt",
            "is_improvement": True,
            "addressed_critiques": ["Added salt", "Using bcrypt instead of MD5"]
        }
    })
    
    # Progress to the REFINE phase
    coordinator.progress_to_phase(Phase.REFINE)
    
    # Execute the REFINE phase
    refine_results = coordinator.execute_current_phase()
    
    # Verify that apply_enhanced_dialectical_reasoning was called
    coordinator.wsde_team.apply_enhanced_dialectical_reasoning.assert_called()
    
    # Verify that the dialectical reasoning results are in the phase results
    assert "dialectical_reasoning" in refine_results
    dialectical = refine_results["dialectical_reasoning"]
    assert "thesis" in dialectical
    assert "antithesis" in dialectical
    assert "synthesis" in dialectical
    
    # Restore the original method
    coordinator.wsde_team.apply_enhanced_dialectical_reasoning = original_dialectical