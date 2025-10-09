"""
Unit tests for the requirement service.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from devsynth.adapters.requirements.memory_repository import (
    InMemoryChangeRepository,
    InMemoryRequirementRepository,
)
from devsynth.application.requirements.models import RequirementUpdateDTO
from devsynth.application.requirements.requirement_service import RequirementService
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


class TestRequirementService(unittest.TestCase):
    """Test cases for the requirement service.

    ReqID: N/A"""

    def setUp(self):
        """Set up test fixtures."""
        self.requirement_repository = InMemoryRequirementRepository()
        self.change_repository = InMemoryChangeRepository()
        self.dialectical_reasoner = MagicMock()
        self.dialectical_reasoner.evaluate_change = MagicMock()
        self.dialectical_reasoner.assess_impact = MagicMock()
        self.notification_service = MagicMock()
        self.service = RequirementService(
            requirement_repository=self.requirement_repository,
            change_repository=self.change_repository,
            dialectical_reasoner=self.dialectical_reasoner,
            notification_service=self.notification_service,
        )

    @pytest.mark.fast
    def test_create_requirement_succeeds(self):
        """Test creating a requirement.

        ReqID: N/A"""
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
        )
        created_requirement = self.service.create_requirement(requirement, "test_user")
        self.assertEqual(created_requirement.title, "Test Requirement")
        self.assertEqual(created_requirement.description, "This is a test requirement")
        self.assertEqual(created_requirement.status, RequirementStatus.DRAFT)
        self.assertEqual(created_requirement.priority, RequirementPriority.MEDIUM)
        self.assertEqual(created_requirement.type, RequirementType.FUNCTIONAL)
        self.assertEqual(created_requirement.created_by, "test_user")
        saved_requirement = self.requirement_repository.get_requirement(
            created_requirement.id
        )
        self.assertIsNotNone(saved_requirement)
        self.assertEqual(saved_requirement.id, created_requirement.id)
        changes = self.change_repository.get_changes_for_requirement(
            created_requirement.id
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, ChangeType.ADD)
        self.assertEqual(changes[0].requirement_id, created_requirement.id)
        self.assertEqual(changes[0].created_by, "test_user")
        self.assertEqual(changes[0].reason, "Initial creation")
        self.assertIsNone(changes[0].previous_state)
        self.assertEqual(changes[0].new_state.id, created_requirement.id)

    @pytest.mark.fast
    def test_update_requirement_succeeds(self):
        """Test updating a requirement.

        ReqID: N/A"""
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
        updates = RequirementUpdateDTO(
            title="Updated Test Requirement",
            description="This is an updated test requirement",
            status=RequirementStatus.PROPOSED,
            priority=RequirementPriority.HIGH,
        )
        updated_requirement = self.service.update_requirement(
            saved_requirement.id, updates, "test_user", "Testing update"
        )
        self.assertEqual(updated_requirement.title, "Updated Test Requirement")
        self.assertEqual(
            updated_requirement.description, "This is an updated test requirement"
        )
        self.assertEqual(updated_requirement.status, RequirementStatus.PROPOSED)
        self.assertEqual(updated_requirement.priority, RequirementPriority.HIGH)
        self.assertEqual(updated_requirement.type, RequirementType.FUNCTIONAL)
        saved_requirement = self.requirement_repository.get_requirement(
            updated_requirement.id
        )
        self.assertIsNotNone(saved_requirement)
        self.assertEqual(saved_requirement.title, "Updated Test Requirement")
        changes = self.change_repository.get_changes_for_requirement(
            updated_requirement.id
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, ChangeType.MODIFY)
        self.assertEqual(changes[0].requirement_id, updated_requirement.id)
        self.assertEqual(changes[0].created_by, "test_user")
        self.assertEqual(changes[0].reason, "Testing update")
        self.assertEqual(changes[0].previous_state.title, "Test Requirement")
        self.assertEqual(changes[0].new_state.title, "Updated Test Requirement")
        self.notification_service.notify_change_proposed.assert_called_once()
        self.dialectical_reasoner.evaluate_change.assert_called_once()
        self.dialectical_reasoner.assess_impact.assert_called_once()

    @pytest.mark.fast
    def test_delete_requirement_succeeds(self):
        """Test deleting a requirement.

        ReqID: N/A"""
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
        deleted = self.service.delete_requirement(
            saved_requirement.id, "test_user", "Testing deletion"
        )
        self.assertTrue(deleted)
        deleted_requirement = self.requirement_repository.get_requirement(
            saved_requirement.id
        )
        self.assertIsNone(deleted_requirement)
        changes = self.change_repository.get_changes_for_requirement(
            saved_requirement.id
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, ChangeType.REMOVE)
        self.assertEqual(changes[0].requirement_id, saved_requirement.id)
        self.assertEqual(changes[0].created_by, "test_user")
        self.assertEqual(changes[0].reason, "Testing deletion")
        self.assertEqual(changes[0].previous_state.id, saved_requirement.id)
        self.assertIsNone(changes[0].new_state)
        self.notification_service.notify_change_proposed.assert_called_once()
        self.dialectical_reasoner.evaluate_change.assert_called_once()
        self.dialectical_reasoner.assess_impact.assert_called_once()

    @pytest.mark.fast
    def test_approve_change_succeeds(self):
        """Test approving a change.

        ReqID: N/A"""
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
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
                created_by="test_user",
            ),
            created_by="test_user",
            reason="Testing approval",
        )
        saved_change = self.change_repository.save_change(change)
        approved_change = self.service.approve_change(saved_change.id, "approver_user")
        self.assertTrue(approved_change.approved)
        self.assertEqual(approved_change.approved_by, "approver_user")
        self.assertIsNotNone(approved_change.approved_at)
        self.notification_service.notify_change_approved.assert_called_once()
        approved_payload = self.notification_service.notify_change_approved.call_args[
            0
        ][0]
        assert approved_payload.change is approved_change

    @pytest.mark.fast
    def test_reject_change_succeeds(self):
        """Test rejecting a change.

        ReqID: N/A"""
        requirement = Requirement(
            title="Test Requirement",
            description="This is a test requirement",
            status=RequirementStatus.DRAFT,
            priority=RequirementPriority.MEDIUM,
            type=RequirementType.FUNCTIONAL,
            created_by="test_user",
        )
        saved_requirement = self.requirement_repository.save_requirement(requirement)
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
                created_by="test_user",
            ),
            created_by="test_user",
            reason="Testing rejection",
        )
        saved_change = self.change_repository.save_change(change)
        rejected_change = self.service.reject_change(
            saved_change.id, "rejector_user", "This change is not necessary"
        )
        self.assertFalse(rejected_change.approved)
        self.assertEqual(len(rejected_change.comments), 1)
        self.assertEqual(
            rejected_change.comments[0], "rejector_user: This change is not necessary"
        )
        self.notification_service.notify_change_rejected.assert_called_once()
        rejected_payload = self.notification_service.notify_change_rejected.call_args[
            0
        ][0]
        assert rejected_payload.change is rejected_change


if __name__ == "__main__":
    unittest.main()
