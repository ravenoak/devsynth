"""
Integration test for the interaction between code analysis components and WSDE.

This test verifies that the code analysis components (ProjectStateAnalyzer,
SelfAnalyzer, CodeTransformer, AstWorkflowIntegration) can be used effectively
within the WSDE framework to analyze and transform code during the development process.
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
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.task import Task, TaskStatus
from devsynth.domain.models.wsde_facade import WSDETeam


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
        if isinstance(task, dict):
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
                    "transformations",
                    ["remove_unused_imports", "remove_unused_variables"],
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
                return {
                    "refined": self.ast_workflow.refine_implementation(code, task_id)
                }
            else:
                return {"error": "Unknown task type"}
        elif isinstance(task, Task):
            task_data = task.data or {}
            if "code" in task_data:
                code = task_data["code"]
                if task.task_type == "analyze":
                    analysis = self.code_analyzer.analyze_code(code)
                    quality_metrics = self.ast_workflow._calculate_complexity(analysis)
                    task.result = {
                        "analysis": analysis,
                        "quality_metrics": quality_metrics,
                    }
                elif task.task_type == "transform":
                    transformations = task_data.get(
                        "transformations",
                        ["remove_unused_imports", "remove_unused_variables"],
                    )
                    transformed = self.code_transformer.transform_code(
                        code, transformations
                    )
                    task.result = {"transformed": transformed}
                elif task.task_type == "refine":
                    refined = self.ast_workflow.refine_implementation(
                        code, str(task.id)
                    )
                    task.result = {"refined": refined}
                else:
                    task.result = {"error": "Unknown task type"}
            else:
                task.result = {"error": "No code provided"}
            task.status = TaskStatus.COMPLETED
            return task
        else:
            return {"error": "Unsupported task format"}


@pytest.fixture
def wsde_team_with_code_analysis(tmp_path_factory):
    """Create a WSDE team with code analysis components."""
    memory_manager = MemoryManager()
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
        code_reviewer_agent = CodeAnalysisAgent(
            "code_reviewer",
            code_analyzer,
            ast_transformer,
            project_analyzer,
            self_analyzer,
            code_transformer,
            ast_workflow,
        )
        wsde_team = WSDETeam(name="TestCodeAnalysisWsdeIntegrationTeam")
        wsde_team.add_agent(code_analysis_agent)
        wsde_team.add_agent(code_reviewer_agent)
        yield wsde_team


@pytest.mark.slow
def test_code_analysis_in_wsde_team_succeeds(wsde_team_with_code_analysis):
    """Test that code analysis can be performed by a WSDE team.

    ReqID: N/A"""

    task_data = {
        "analyze_code": """
def calculate_sum(a, b):
    result = a + b
    return result
        """
    }
    code_analyst = wsde_team_with_code_analysis.get_agent("code_analyst")
    result = code_analyst.process(task_data)
    assert "analysis" in result
    assert "quality_metrics" in result
    analysis = result["analysis"]
    assert analysis.get_functions()[0]["name"] == "calculate_sum"
    quality_metrics = result["quality_metrics"]
    assert 0 <= quality_metrics <= 1


@pytest.mark.slow
def test_code_transformation_in_wsde_team_succeeds(wsde_team_with_code_analysis):
    """Test that code transformation can be performed by a WSDE team.

    ReqID: N/A"""
    task_data = {
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
        "transformations": ["remove_unused_imports", "remove_unused_variables"],
    }
    code_analyst = wsde_team_with_code_analysis.get_agent("code_analyst")
    result = code_analyst.process(task_data)
    assert "transformed" in result
    transformed = result["transformed"]
    assert "import re" not in transformed.transformed_code
    assert "z = 15" not in transformed.transformed_code


@pytest.mark.slow
def test_code_review_collaboration_in_wsde_team_succeeds(wsde_team_with_code_analysis):
    """Test that code analysis agents can collaborate in a WSDE team.

    ReqID: N/A"""
    code = """
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
    """
    analysis_task = Task(
        id="task1", task_type="analyze", data={"code": code}, assigned_to="code_analyst"
    )
    review_task = Task(
        id="task2",
        task_type="transform",
        data={"code": code, "transformations": ["remove_unused_variables"]},
        assigned_to="code_reviewer",
    )
    wsde_team_with_code_analysis.process_task(analysis_task)
    wsde_team_with_code_analysis.process_task(review_task)
    assert analysis_task.status == TaskStatus.COMPLETED
    assert review_task.status == TaskStatus.COMPLETED
    assert "analysis" in analysis_task.result
    assert "quality_metrics" in analysis_task.result
    assert "transformed" in review_task.result
    transformed = review_task.result["transformed"]
    assert "z = 15" not in transformed.transformed_code


@pytest.mark.slow
def test_code_refinement_in_wsde_team_succeeds(wsde_team_with_code_analysis):
    """Test that code refinement can be performed by a WSDE team.

    ReqID: N/A"""
    task_data = {
        "refine_implementation": """
def calculate(a, b):
    # Redundant variable
    result = a + b
    return result
        """,
        "task_id": "test_refinement",
    }
    code_analyst = wsde_team_with_code_analysis.get_agent("code_analyst")
    result = code_analyst.process(task_data)
    assert "refined" in result
    refined = result["refined"]
    assert isinstance(refined, RefinementResult)
    assert refined.original_code.strip().startswith("def calculate")
    assert refined.refined_code.strip()
    assert isinstance(refined.improvements, list)
