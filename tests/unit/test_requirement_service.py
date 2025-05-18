
"""
Unit tests for the requirement service.
"""
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from devsynth.domain.models.requirement import (
    ChangeType, Requirement, RequirementChange, RequirementPriority,
    RequirementStatus, RequirementType
)
from devsynth.application.requirements.requirement_service import RequirementService
from devsynth.adapters.requirements.memory_repository import (
    InMemoryChangeRepository, InMemoryRequirementRepository
)


class TestRequirementService(unittest.TestCase):
    """Test cases for the requirement service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock repositories
        self.requirement_repository = InMemoryRequirementRepository()
        self.change_repository = InMemoryChangeRepository()
        
        # Create mock dialectical reasoner
        self.dialectical_reasoner = MagicMock()
        self.dialectical_reasoner.evaluate_change = MagicMock()
        self.dialectical_reasoner.assess_impact = MagicMock()
        
        # Create mock notification service
        self.notification_service = MagicMock()
        
        # Create the requirement service
        self.service = RequirementService(
            requirement_repository=self.requirement_repository,
            change_repository=self.change_repository,
            dialectical_reasoner=self.dialectical_reasoner,
            notification_service=self.notification_service
        )
    
    def test_create_requirement(self):
        """Test creating a requirement."""
        # Create a requirement
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL
        )
        
        # Create the requirement using the service
        created_requirement = self.service.create_requirement(requirement, "test_user")
        
        # Verify the created requirement
        self.assertEqual(created_requirement.title, "Test Requirement")
        self.assertEqual(created_requirement.description, "This is a test requirement")
        self.assertEqual(created_requirement.status, RequirementStatus.DRAFT)
        self.assertEqual(created_requirement.priority, RequirementPriority.MEDIUM)
        self.assertEqual(created_requirement.type, RequirementType.FUNCTIONAL)
        self.assertEqual(created_requirement.created_by, "test_user")
        
        # Verify that the requirement was saved
        saved_requirement = self.requirement_repository.get_requirement(created_requirement.id)
        self.assertIsNotNone(saved_requirement)
        self.assertEqual(saved_requirement.id, created_requirement.id)
        
        # Verify that a change record was created
        changes = self.change_repository.get_changes_for_requirement(created_requirement.id)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, ChangeType.ADD)
        self.assertEqual(changes[0].requirement_id, created_requirement.id)
        self.assertEqual(changes[0].created_by, "test_user")
        self.assertEqual(changes[0].reason, "Initial creation")
        self.assertIsNone(changes[0].previous_state)
        self.assertEqual(changes[0].new_state.id, created_requirement.id)
    
    def test_update_requirement(self):
        """Test updating a requirement."""
        # Create a requirement
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user"
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
        
        # Update the requirement
        updates = {
            "title": "Updated Test Requirement",
            "description": "This is an updated test requirement",
            "status": RequirementStatus.PROPOSED,
            "priority": RequirementPriority.HIGH
        }
        
        updated_requirement = self.service.update_requirement(
            saved_requirement.id, updates, "test_user", "Testing update"
        )
        
        # Verify the updated requirement
        self.assertEqual(updated_requirement.title, "Updated Test Requirement")
        self.assertEqual(updated_requirement.description, "This is an updated test requirement")
        self.assertEqual(updated_requirement.status, RequirementStatus.PROPOSED)
        self.assertEqual(updated_requirement.priority, RequirementPriority.HIGH)
        self.assertEqual(updated_requirement.type, RequirementType.FUNCTIONAL)  # Unchanged
        
        # Verify that the requirement was saved
        saved_requirement = self.requirement_repository.get_requirement(updated_requirement.id)
        self.assertIsNotNone(saved_requirement)
        self.assertEqual(saved_requirement.title, "Updated Test Requirement")
        
        # Verify that a change record was created
        changes = self.change_repository.get_changes_for_requirement(updated_requirement.id)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, ChangeType.MODIFY)
        self.assertEqual(changes[0].requirement_id, updated_requirement.id)
        self.assertEqual(changes[0].created_by, "test_user")
        self.assertEqual(changes[0].reason, "Testing update")
        self.assertEqual(changes[0].previous_state.title, "Test Requirement")
        self.assertEqual(changes[0].new_state.title, "Updated Test Requirement")
        
        # Verify that the notification service was called
        self.notification_service.notify_change_proposed.assert_called_once()
        
        # Verify that the dialectical reasoner was called
        self.dialectical_reasoner.evaluate_change.assert_called_once()
        self.dialectical_reasoner.assess_impact.assert_called_once()
    
    def test_delete_requirement(self):
        """Test deleting a requirement."""
        # Create a requirement
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user"
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
        
        # Delete the requirement
        deleted = self.service.delete_requirement(
            saved_requirement.id, "test_user", "Testing deletion"
        )
        
        # Verify that the requirement was deleted
        self.assertTrue(deleted)
        deleted_requirement = self.requirement_repository.get_requirement(saved_requirement.id)
        self.assertIsNone(deleted_requirement)
        
        # Verify that a change record was created
        changes = self.change_repository.get_changes_for_requirement(saved_requirement.id)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, ChangeType.REMOVE)
        self.assertEqual(changes[0].requirement_id, saved_requirement.id)
        self.assertEqual(changes[0].created_by, "test_user")
        self.assertEqual(changes[0].reason, "Testing deletion")
        self.assertEqual(changes[0].previous_state.id, saved_requirement.id)
        self.assertIsNone(changes[0].new_state)
        
        # Verify that the notification service was called
        self.notification_service.notify_change_proposed.assert_called_once()
        
        # Verify that the dialectical reasoner was called
        self.dialectical_reasoner.evaluate_change.assert_called_once()
        self.dialectical_reasoner.assess_impact.assert_called_once()
    
    def test_approve_change(self):
        """Test approving a change."""
        # Create a requirement
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user"
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
        
        # Create a change
        change = RequirementChange(
            requirement_id=saved_requirement.id,
            change_type=ChangeType.MODIFY,
            previous_state=saved_requirement,
            new_state=Requirement(
                id=saved_requirement.id,
                title="Updated Test Requirement",
                description="This is an updated test requirement",
                status=RequirementStatus.PROPOSED,
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                created_by="test_user"
            ),
            created_by="test_user",
            reason="Testing approval"
        )
        saved_change = self.change_repository.save_change(change)
        
        # Approve the change
        approved_change = self.service.approve_change(saved_change.id, "approver_user")
        
        # Verify the approved change
        self.assertTrue(approved_change.approved)
        self.assertEqual(approved_change.approved_by, "approver_user")
        self.assertIsNotNone(approved_change.approved_at)
        
        # Verify that the notification service was called
        self.notification_service.notify_change_approved.assert_called_once_with(approved_change)
    
    def test_reject_change(self):
        """Test rejecting a change."""
        # Create a requirement
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user"
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
        
        # Create a change
        change = RequirementChange(
            requirement_id=saved_requirement.id,
            change_type=ChangeType.MODIFY,
            previous_state=saved_requirement,
            new_state=Requirement(
                id=saved_requirement.id,
                title="Updated Test Requirement",
                description="This is an updated test requirement",
                status=RequirementStatus.PROPOSED,
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                created_by="test_user"
            ),
            created_by="test_user",
            reason="Testing rejection"
        )
        saved_change = self.change_repository.save_change(change)
        
        # Reject the change
        rejected_change = self.service.reject_change(
            saved_change.id, "rejector_user", "This change is not necessary"
        )
        
        # Verify the rejected change
        self.assertFalse(rejected_change.approved)
        self.assertEqual(len(rejected_change.comments), 1)
        self.assertEqual(rejected_change.comments[0], "rejector_user: This change is not necessary")
        
        # Verify that the notification service was called
        self.notification_service.notify_change_rejected.assert_called_once_with(rejected_change)


if __name__ == "__main__":
    unittest.main()
