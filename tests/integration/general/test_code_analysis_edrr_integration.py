"""
Integration test for the interaction between code analysis components and EDRR.

This test verifies that the code analysis components (ProjectStateAnalyzer,
SelfAnalyzer, CodeTransformer, AstWorkflowIntegration) can be used effectively
within the EDRR framework to analyze and transform code during the development process.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.code_analysis.ast_workflow_integration import (
    AstWorkflowIntegration,
    RefinementResult,
)
from devsynth.application.code_analysis.project_state_analyzer import (
    ProjectStateAnalyzer,
)
from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer
from devsynth.application.code_analysis.transformer import CodeTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.mark.slow
def test_agent_type_expert_exists():
    """Ensure the EXPERT enum is defined."""
    assert AgentType.EXPERT.value == "expert"


class CodeAnalysisAgent(UnifiedAgent):
    """An agent that uses code analysis components to analyze and transform code."""

    def __init__(
        self,
        name,
        code_analyzer,
        ast_transformer,
        project_analyzer,
        self_analyzer,
        code_transformer,
        ast_workflow,
    ):
        """Initialize the agent with code analysis components."""
        super().__init__()
        self.initialize(
            AgentConfig(
                name=name,
                agent_type=AgentType.EXPERT,
                description="Code analysis expert agent",
                capabilities=["code analysis", "refactoring", "architecture"],
                parameters={
                    "expertise": ["code analysis", "refactoring", "architecture"]
                },
            )
        )
        self.code_analyzer = code_analyzer
        self.ast_transformer = ast_transformer
        self.project_analyzer = project_analyzer
        self.self_analyzer = self_analyzer
        self.code_transformer = code_transformer
        self.ast_workflow = ast_workflow

    def process(self, task):
        """Process a task using code analysis components."""
        if "analyze_code" in task:
            code = task["analyze_code"]
            return {
                "analysis": self.code_analyzer.analyze_code(code),
                "quality_metrics": self.ast_workflow._calculate_complexity(
                    self.code_analyzer.analyze_code(code)
                ),
            }
        elif "transform_code" in task:
            code = task["transform_code"]
            transformations = task.get(
                "transformations", ["remove_unused_imports", "remove_unused_variables"]
            )
            return {
                "transformed": self.code_transformer.transform_code(
                    code, transformations
                )
            }
        elif "analyze_project" in task:
            project_path = task["analyze_project"]
            return {"project_analysis": self.project_analyzer.analyze()}
        elif "analyze_self" in task:
            return {"self_analysis": self.self_analyzer.analyze()}
        elif "refine_implementation" in task:
            code = task["refine_implementation"]
            task_id = task.get("task_id", "test_task")
            return {"refined": self.ast_workflow.refine_implementation(code, task_id)}
        else:
            return {"error": "Unknown task type"}


@pytest.fixture
def code_analysis_coordinator(tmp_path_factory):
    """Create an EDRR coordinator with code analysis components."""
    memory_manager = MemoryManager()
    memory_manager.store = MagicMock(return_value="memid")
    code_analyzer = CodeAnalyzer()
    ast_transformer = AstTransformer()
    with pytest.MonkeyPatch.context() as mp:
        temp_dir = tmp_path_factory.getbasetemp()
        project_file = temp_dir.joinpath("test_project")
        project_file.write_text("# Test project")
        project_path = str(project_file)
        mp.setenv("DEVSYNTH_PROJECT_DIR", project_path)
        project_analyzer = ProjectStateAnalyzer(project_path)
        self_analyzer = SelfAnalyzer(project_path)
        code_transformer = CodeTransformer()
        ast_workflow = AstWorkflowIntegration(memory_manager)
        code_analysis_agent = CodeAnalysisAgent(
            "code_analyst",
            code_analyzer,
            ast_transformer,
            project_analyzer,
            self_analyzer,
            code_transformer,
            ast_workflow,
        )
        wsde_team = WSDETeam(name="TestCodeAnalysisEdrrIntegrationTeam")
        wsde_team.add_agent(code_analysis_agent)
        wsde_team.get_agent = lambda n: next(
            (a for a in wsde_team.agents if getattr(a.config, "name", "") == n),
            None,
        )
        prompt_manager = PromptManager()
        doc_manager = DocumentationManager(memory_manager)
        coordinator = EnhancedEDRRCoordinator(
            memory_manager=memory_manager,
            wsde_team=wsde_team,
            code_analyzer=code_analyzer,
            ast_transformer=ast_transformer,
            prompt_manager=prompt_manager,
            documentation_manager=doc_manager,
        )
        yield coordinator


@pytest.mark.slow
def test_code_analysis_in_edrr_workflow_succeeds(code_analysis_coordinator):
    """Test that code analysis components can be used in an EDRR workflow.

    ReqID: N/A"""

    task = {
        "analyze_code": """
def calculate_sum(a, b):
    result = a + b
    return result
        """
    }
    with patch(
        "devsynth.application.edrr.edrr_coordinator_enhanced.EnhancedEDRRCoordinator._get_llm_response"
    ) as mock_llm:
        mock_llm.return_value = "This code looks good."
        result = code_analysis_coordinator.execute_single_agent_task(
            task=task, agent_name="code_analyst", phase=Phase.ANALYSIS
        )
        assert "analysis" in result
        assert "quality_metrics" in result
        analysis = result["analysis"]
        assert analysis.get_functions()[0]["name"] == "calculate_sum"
        quality_metrics = result["quality_metrics"]
        assert 0 <= quality_metrics <= 1


@pytest.mark.slow
def test_code_transformation_in_edrr_workflow_succeeds(code_analysis_coordinator):
    """Test that code transformation can be performed in an EDRR workflow.

    ReqID: N/A"""
    task = {
        "transform_code": """
import os
import sys
import re  # This import is unused

def calculate_sum(a, b):
    # Redundant assignment
    result = a + b
    return result

def main():
    x = 5
    y = 10
    z = 15  # This variable is unused
    total = calculate_sum(x, y)
    print(f"The sum is {total}")
        """,
        "transformations": ["unused_imports", "unused_variables"],
    }
    with patch(
        "devsynth.application.edrr.edrr_coordinator_enhanced.EnhancedEDRRCoordinator._get_llm_response"
    ) as mock_llm:
        mock_llm.return_value = "Code has been transformed."
        result = code_analysis_coordinator.execute_single_agent_task(
            task=task, agent_name="code_analyst", phase=Phase.IMPLEMENTATION
        )
        assert "transformed" in result
        transformed = result["transformed"]
        assert "import re" not in transformed.get_transformed_code()
        assert "z = 15" not in transformed.get_transformed_code()


@pytest.mark.slow
def test_code_refinement_in_edrr_workflow_succeeds(code_analysis_coordinator):
    """Test that code refinement can be performed in an EDRR workflow.

    ReqID: N/A"""
    task = {
        "refine_implementation": """
def calculate(a, b):
    # Redundant variable
    result = a + b
    return result
        """,
        "task_id": "test_refinement",
    }
    with patch(
        "devsynth.application.edrr.edrr_coordinator_enhanced.EnhancedEDRRCoordinator._get_llm_response"
    ) as mock_llm:
        mock_llm.return_value = "Code has been refined."
        result = code_analysis_coordinator.execute_single_agent_task(
            task=task, agent_name="code_analyst", phase=Phase.REFINEMENT
        )
        assert "refined" in result
        refined = result["refined"]
        assert isinstance(refined, RefinementResult)
        assert refined.original_code.strip().startswith("def calculate")
        assert refined.refined_code.strip()
        assert isinstance(refined.improvements, list)
