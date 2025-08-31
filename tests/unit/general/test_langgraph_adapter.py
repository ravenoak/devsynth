import os
import pickle
from unittest.mock import MagicMock, mock_open, patch

import pytest

from devsynth.adapters.orchestration.langgraph_adapter import (
    FileSystemCheckpointSaver,
    FileSystemWorkflowRepository,
    LangGraphWorkflowEngine,
    NeedsHumanInterventionError,
    WorkflowState,
)
from devsynth.domain.models.workflow import Workflow, WorkflowStatus, WorkflowStep


class TestWorkflowState:
    """Tests for the WorkflowState class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_workflow_state_creation_succeeds(self):
        """Test creating a workflow state.

        ReqID: N/A"""
        state = WorkflowState(
            workflow_id="test-id", command="init", project_root="/path/to/project"
        )
        assert state.workflow_id == "test-id"
        assert state.command == "init"
        assert state.project_root == "/path/to/project"
        assert state.status == WorkflowStatus.PENDING.value
        assert state.needs_human is False
        assert state.human_message == ""
        assert state.context == {}
        assert state.messages == []
        assert state.current_step is None
        assert state.result == {}

    @pytest.mark.fast
    def test_workflow_state_to_dict_succeeds(self):
        """Test converting workflow state to dictionary.

        ReqID: N/A"""
        state = WorkflowState(
            workflow_id="test-id",
            command="init",
            project_root="/path/to/project",
            context={"key": "value"},
            current_step="step-1",
        )
        state_dict = state.to_dict()
        assert state_dict["workflow_id"] == "test-id"
        assert state_dict["command"] == "init"
        assert state_dict["project_root"] == "/path/to/project"
        assert state_dict["context"] == {"key": "value"}
        assert state_dict["current_step"] == "step-1"
        assert state_dict["status"] == WorkflowStatus.PENDING.value

    @pytest.mark.fast
    def test_workflow_state_from_dict_succeeds(self):
        """Test creating workflow state from dictionary.

        ReqID: N/A"""
        state_dict = {
            "workflow_id": "test-id",
            "command": "init",
            "project_root": "/path/to/project",
            "context": {"key": "value"},
            "current_step": "step-1",
            "status": WorkflowStatus.RUNNING.value,
            "needs_human": True,
            "human_message": "Need input",
            "messages": [{"role": "system", "content": "test"}],
            "result": {"success": True},
        }
        state = WorkflowState.from_dict(state_dict)
        assert state.workflow_id == "test-id"
        assert state.command == "init"
        assert state.project_root == "/path/to/project"
        assert state.context == {"key": "value"}
        assert state.current_step == "step-1"
        assert state.status == WorkflowStatus.RUNNING.value
        assert state.needs_human is True
        assert state.human_message == "Need input"
        assert state.messages == [{"role": "system", "content": "test"}]
        assert state.result == {"success": True}


class TestFileSystemCheckpointSaver:
    """Tests for the FileSystemCheckpointSaver class.

    ReqID: N/A"""

    @pytest.fixture
    def checkpoint_saver(self, tmp_path):
        """Create a checkpoint saver with a temporary directory."""
        checkpoint_dir = str(tmp_path / "checkpoints")
        return FileSystemCheckpointSaver(checkpoint_dir)

    @pytest.mark.fast
    def test_checkpoint_path_succeeds(self, checkpoint_saver):
        """Test getting checkpoint path.

        ReqID: N/A"""
        path = checkpoint_saver.get_checkpoint_path("test-thread")
        assert path.endswith("test-thread.pkl")

    @pytest.mark.fast
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pickle.load")
    def test_get_checkpoint_exists_succeeds(
        self, mock_pickle_load, mock_file_open, mock_exists, checkpoint_saver
    ):
        """Test getting an existing checkpoint.

        ReqID: N/A"""
        mock_exists.return_value = True
        mock_pickle_load.return_value = {"state": "test"}
        result = checkpoint_saver.get({"configurable": {"thread_id": "test-thread"}})
        assert result == {"state": "test"}
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()
        mock_pickle_load.assert_called_once()

    @pytest.mark.fast
    @patch("os.path.exists")
    def test_get_checkpoint_not_exists_succeeds(self, mock_exists, checkpoint_saver):
        """Test getting a non-existent checkpoint.

        ReqID: N/A"""
        mock_exists.return_value = False
        result = checkpoint_saver.get({"configurable": {"thread_id": "test-thread"}})
        assert result is None
        mock_exists.assert_called_once()

    @pytest.mark.fast
    @patch("builtins.open", new_callable=mock_open)
    @patch("pickle.dump")
    def test_put_checkpoint_succeeds(
        self, mock_pickle_dump, mock_file_open, checkpoint_saver
    ):
        """Test saving a checkpoint.

        ReqID: N/A"""
        checkpoint = {"state": "test"}
        checkpoint_saver.put(
            {"configurable": {"thread_id": "test-thread"}}, checkpoint, {}, {}
        )
        mock_file_open.assert_called_once()
        mock_pickle_dump.assert_called_once_with(checkpoint, mock_file_open())


class TestLangGraphWorkflowEngine:
    """Tests for the LangGraphWorkflowEngine class.

    ReqID: N/A"""

    @pytest.fixture
    def workflow_engine(self):
        """Create a workflow engine with a mock human intervention callback."""
        callback = MagicMock()
        return LangGraphWorkflowEngine(human_intervention_callback=callback)

    @pytest.mark.fast
    def test_create_workflow_succeeds(self, workflow_engine):
        """Test creating a workflow.

        ReqID: N/A"""
        workflow = workflow_engine.create_workflow("test-workflow", "Test workflow")
        assert workflow.id is not None
        assert workflow.name == "test-workflow"
        assert workflow.description == "Test workflow"
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.steps == []

    @pytest.mark.fast
    def test_add_step_succeeds(self, workflow_engine):
        """Test adding a step to a workflow.

        ReqID: N/A"""
        workflow = workflow_engine.create_workflow("test-workflow", "Test workflow")
        step = WorkflowStep(
            id="step-1",
            name="Test Step",
            description="A test step",
            agent_type="test_agent",
        )
        updated_workflow = workflow_engine.add_step(workflow, step)
        assert len(updated_workflow.steps) == 1
        assert updated_workflow.steps[0].id == "step-1"
        assert updated_workflow.steps[0].name == "Test Step"
        assert updated_workflow.steps[0].status == WorkflowStatus.PENDING

    @pytest.mark.fast
    @patch("devsynth.adapters.orchestration.langgraph_adapter.StateGraph")
    @patch("devsynth.adapters.orchestration.langgraph_adapter.Pregel")
    def test_execute_workflow_succeeds(
        self, mock_pregel, mock_state_graph, workflow_engine
    ):
        """Test executing a workflow.

        ReqID: N/A"""
        workflow = workflow_engine.create_workflow("test-workflow", "Test workflow")
        step = WorkflowStep(
            id="step-1",
            name="Test Step",
            description="A test step",
            agent_type="test_agent",
        )
        workflow = workflow_engine.add_step(workflow, step)
        mock_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_graph_instance
        mock_graph_instance.compile.return_value = MagicMock()
        mock_executor = MagicMock()
        mock_pregel.return_value = mock_executor
        mock_executor.invoke.return_value = WorkflowState(
            workflow_id=workflow.id,
            command="test",
            project_root="/path/to/project",
            status=WorkflowStatus.COMPLETED.value,
            result={"success": True},
        ).to_dict()
        result = workflow_engine.execute_workflow(workflow, {"test": "value"})
        assert result.status == WorkflowStatus.COMPLETED
        assert len(mock_state_graph.mock_calls) > 0
        assert len(mock_graph_instance.mock_calls) > 0


class TestFileSystemWorkflowRepository:
    """Tests for the FileSystemWorkflowRepository class.

    ReqID: N/A"""

    @pytest.fixture
    def workflow_repo(self, tmp_path):
        """Create a workflow repository with a temporary directory."""
        repo_dir = str(tmp_path / "workflows")
        return FileSystemWorkflowRepository(repo_dir)

    @pytest.mark.fast
    def test_save_and_get_workflow_succeeds(self, workflow_repo):
        """Test saving and retrieving a workflow.

        ReqID: N/A"""
        workflow = Workflow(
            id="test-id",
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.PENDING,
            steps=[],
        )
        with patch("builtins.open", new_callable=mock_open) as mock_file:
            workflow_repo.save(workflow)
            mock_file.assert_called_once()
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", new_callable=mock_open) as mock_file,
            patch("pickle.load", return_value=workflow),
        ):
            retrieved = workflow_repo.get("test-id")
            assert retrieved.id == "test-id"
            assert retrieved.name == "Test Workflow"
            mock_file.assert_called_once()

    @pytest.mark.fast
    def test_list_workflows_succeeds(self, workflow_repo):
        """Test listing workflows.

        ReqID: N/A"""
        mock_files = ["workflow1.pkl", "workflow2.pkl", "not_a_workflow.txt"]
        workflow1 = Workflow(
            id="workflow1",
            name="Workflow 1",
            description="",
            status=WorkflowStatus.COMPLETED,
            steps=[],
        )
        workflow2 = Workflow(
            id="workflow2",
            name="Workflow 2",
            description="",
            status=WorkflowStatus.RUNNING,
            steps=[],
        )
        with patch.object(
            FileSystemWorkflowRepository, "list", return_value=[workflow1, workflow2]
        ):
            workflows = workflow_repo.list()
            assert len(workflows) == 2
            assert workflows[0].id == "workflow1"
            assert workflows[1].id == "workflow2"
        with patch.object(
            FileSystemWorkflowRepository, "list", return_value=[workflow1]
        ):
            completed_workflows = workflow_repo.list(
                {"status": WorkflowStatus.COMPLETED}
            )
            assert len(completed_workflows) == 1
            assert completed_workflows[0].id == "workflow1"
