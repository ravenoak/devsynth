"""
Integration test for WSDE peer review memory integration.

This test verifies that the memory_manager is properly passed from the AgentAdapter
to the WSDETeamCoordinator to the WSDETeam to the PeerReview, and that the PeerReview
correctly stores data in the memory system.
"""

import pytest
from unittest.mock import MagicMock, patch

from devsynth.adapters.agents.agent_adapter import AgentAdapter, WSDETeamCoordinator
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.collaboration.peer_review import PeerReview


class MockMemoryAdapter:
    """Mock memory adapter for testing."""

    def __init__(self):
        self.items = {}
        self.update_calls = []
        self.queue_update_calls = []

    def update(self, item):
        """Mock update method."""
        self.items[item.id] = item
        self.update_calls.append(item)
        return item.id

    def queue_update(self, item):
        """Mock queue_update method."""
        self.items[item.id] = item
        self.queue_update_calls.append(item)
        return item.id

    def retrieve(self, item_id):
        """Mock retrieve method."""
        return self.items.get(item_id)

    def search(self, query, limit=10):
        """Mock search method."""
        return []


@pytest.fixture
def memory_adapter():
    """Create a mock memory adapter."""
    return MockMemoryAdapter()


@pytest.fixture
def memory_manager(memory_adapter):
    """Create a memory manager with the mock adapter."""
    manager = MemoryManager(adapters={"tinydb": memory_adapter})
    return manager


@pytest.fixture
def agent_adapter(memory_manager):
    """Create an agent adapter with the memory manager."""
    return AgentAdapter(memory_manager=memory_manager)


@pytest.fixture
def wsde_team(agent_adapter):
    """Create a WSDE team using the agent adapter."""
    team = agent_adapter.create_team("test_team")
    
    # Add author agent
    author = UnifiedAgent()
    author.initialize(
        AgentConfig(name="author", agent_type=AgentType.ORCHESTRATOR)
    )
    agent_adapter.add_agent_to_team(author)
    
    # Add reviewer agents
    for i in range(2):
        reviewer = UnifiedAgent()
        reviewer.initialize(
            AgentConfig(name=f"reviewer{i}", agent_type=AgentType.ORCHESTRATOR)
        )
        reviewer.process = MagicMock(return_value={"feedback": f"feedback from reviewer{i}"})
        agent_adapter.add_agent_to_team(reviewer)
    
    return team


def test_memory_manager_passed_to_team(agent_adapter, memory_manager):
    """Test that the memory_manager is passed to the team."""
    team = agent_adapter.create_team("test_team")
    assert hasattr(team, "memory_manager")
    assert team.memory_manager is memory_manager


def test_memory_manager_passed_to_peer_review(wsde_team, memory_manager):
    """Test that the memory_manager is passed to the peer review."""
    # Get author and reviewers
    author = wsde_team.agents[0]
    reviewers = wsde_team.agents[1:]
    
    # Create a work product
    work_product = {"text": "Test work product"}
    
    # Request peer review
    review = wsde_team.request_peer_review(work_product, author, reviewers)
    
    # Verify memory_manager is passed to the peer review
    assert hasattr(review, "memory_manager")
    assert review.memory_manager is memory_manager


def test_peer_review_stores_in_memory(wsde_team, memory_manager, memory_adapter):
    """Test that the peer review stores data in memory."""
    # Get author and reviewers
    author = wsde_team.agents[0]
    reviewers = wsde_team.agents[1:]
    
    # Create a work product
    work_product = {"text": "Test work product"}
    
    # Request peer review
    review = wsde_team.request_peer_review(work_product, author, reviewers)
    
    # Verify that the review is stored in memory during assign_reviews
    assert len(memory_adapter.update_calls) > 0 or len(memory_adapter.queue_update_calls) > 0
    
    # Find the stored review
    stored_review = None
    for item in memory_adapter.items.values():
        if item.memory_type == MemoryType.PEER_REVIEW:
            stored_review = item
            break
    
    assert stored_review is not None
    assert stored_review.content.get("review_id") == review.review_id


def test_full_peer_review_workflow_with_memory(wsde_team, memory_manager, memory_adapter):
    """Test the full peer review workflow with memory integration."""
    # Get author and reviewers
    author = wsde_team.agents[0]
    reviewers = wsde_team.agents[1:]
    
    # Create a work product
    work_product = {"text": "Test work product"}
    
    # Mock the build_consensus method to return a predefined result
    wsde_team.build_consensus = MagicMock(
        return_value={
            "method": "majority_opinion",
            "majority_opinion": "approve",
            "agent_opinions": {
                "reviewer0": {"opinion": "approve", "rationale": ""},
                "reviewer1": {"opinion": "approve", "rationale": ""},
            },
        }
    )
    
    # Request peer review
    review = wsde_team.request_peer_review(work_product, author, reviewers)
    
    # Collect reviews
    review.collect_reviews()
    
    # Aggregate feedback
    feedback = review.aggregate_feedback()
    
    # Finalize the review
    result = review.finalize(approved=True)
    
    # Verify that the review is stored in memory at each step
    assert len(memory_adapter.items) >= 3  # At least 3 updates: assign, collect, finalize
    
    # Verify that the final result contains the expected data
    assert result["status"] == "approved"
    assert "feedback" in result
    assert "review_id" in result
    
    # Verify that the consensus result is included
    assert "consensus" in result
    assert result["consensus"]["method"] == "majority_opinion"
    assert result["consensus"]["majority_opinion"] == "approve"


def test_cross_store_synchronization(wsde_team, memory_manager):
    """Test cross-store synchronization for peer review."""
    # Create a second mock adapter
    second_adapter = MockMemoryAdapter()
    memory_manager.adapters["graph"] = second_adapter
    
    # Enable sync manager
    memory_manager.sync_manager = MagicMock()
    memory_manager.sync_manager.begin_transaction = MagicMock(return_value=True)
    memory_manager.sync_manager.commit_transaction = MagicMock(return_value=True)
    
    # Get author and reviewers
    author = wsde_team.agents[0]
    reviewers = wsde_team.agents[1:]
    
    # Create a work product
    work_product = {"text": "Test work product"}
    
    # Request peer review with immediate sync
    with patch('devsynth.application.collaboration.peer_review.PeerReview.store_in_memory') as mock_store:
        review = wsde_team.request_peer_review(work_product, author, reviewers)
        review.store_in_memory(immediate_sync=True)
    
    # Verify that store_in_memory was called with immediate_sync=True
    mock_store.assert_called_with(immediate_sync=True)
    
    # Verify that the sync manager was used
    memory_manager.sync_manager.begin_transaction.assert_called()
    memory_manager.sync_manager.commit_transaction.assert_called()