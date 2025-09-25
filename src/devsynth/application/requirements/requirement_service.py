"""
Service for requirements management.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
    RequirementStatus,
)
from devsynth.ports.requirement_port import (
    ChangeRepositoryPort,
    DialecticalReasonerPort,
    NotificationPort,
    RequirementRepositoryPort,
)


def determine_edrr_phase(change: RequirementChange) -> str:
    """Return the appropriate EDRR phase for a requirement change."""

    change_type = getattr(change, "change_type", None)
    if change_type == ChangeType.ADD:
        return "EXPAND"
    if change_type == ChangeType.REMOVE:
        return "RETROSPECT"
    return "REFINE"


class RequirementService:
    """
    Service for managing requirements.
    """

    def __init__(
        self,
        requirement_repository: RequirementRepositoryPort,
        change_repository: ChangeRepositoryPort,
        dialectical_reasoner: DialecticalReasonerPort,
        notification_service: NotificationPort,
    ):
        """
        Initialize the requirement service.

        Args:
            requirement_repository: Repository for requirements.
            change_repository: Repository for requirement changes.
            dialectical_reasoner: Service for dialectical reasoning.
            notification_service: Service for sending notifications.
        """
        self.requirement_repository = requirement_repository
        self.change_repository = change_repository
        self.dialectical_reasoner = dialectical_reasoner
        self.notification_service = notification_service

    def get_requirement(self, requirement_id: UUID) -> Optional[Requirement]:
        """
        Get a requirement by ID.

        Args:
            requirement_id: The ID of the requirement.

        Returns:
            The requirement if found, None otherwise.
        """
        return self.requirement_repository.get_requirement(requirement_id)

    def get_all_requirements(self) -> List[Requirement]:
        """
        Get all requirements.

        Returns:
            A list of all requirements.
        """
        return self.requirement_repository.get_all_requirements()

    def create_requirement(self, requirement: Requirement, user_id: str) -> Requirement:
        """
        Create a new requirement.

        Args:
            requirement: The requirement to create.
            user_id: The ID of the user creating the requirement.

        Returns:
            The created requirement.
        """
        # Set the created_by field
        requirement.created_by = user_id

        # Save the requirement
        saved_requirement = self.requirement_repository.save_requirement(requirement)

        # Create a change record
        change = RequirementChange(
            requirement_id=saved_requirement.id,
            change_type=ChangeType.ADD,
            new_state=saved_requirement,
            created_by=user_id,
            reason="Initial creation",
        )
        self.change_repository.save_change(change)

        return saved_requirement

    def update_requirement(
        self, requirement_id: UUID, updates: dict, user_id: str, reason: str
    ) -> Optional[Requirement]:
        """
        Update a requirement.

        Args:
            requirement_id: The ID of the requirement to update.
            updates: The updates to apply.
            user_id: The ID of the user updating the requirement.
            reason: The reason for the update.

        Returns:
            The updated requirement if found, None otherwise.
        """
        # Get the requirement
        requirement = self.requirement_repository.get_requirement(requirement_id)
        if not requirement:
            return None

        # Create a copy of the previous state
        previous_state = Requirement(
            id=requirement.id,
            title=requirement.title,
            description=requirement.description,
            status=requirement.status,
            priority=requirement.priority,
            type=requirement.type,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at,
            created_by=requirement.created_by,
            dependencies=requirement.dependencies.copy(),
            tags=requirement.tags.copy(),
            metadata=requirement.metadata.copy(),
        )

        # Update the requirement
        requirement.update(**updates)

        # Create a change record
        change = RequirementChange(
            requirement_id=requirement.id,
            change_type=ChangeType.MODIFY,
            previous_state=previous_state,
            new_state=requirement,
            created_by=user_id,
            reason=reason,
        )
        self.change_repository.save_change(change)

        # Notify about the proposed change
        self.notification_service.notify_change_proposed(change)

        # Evaluate the change using dialectical reasoning
        reasoning = self.dialectical_reasoner.evaluate_change(
            change, edrr_phase=determine_edrr_phase(change)
        )

        # Assess the impact of the change
        impact = self.dialectical_reasoner.assess_impact(
            change, edrr_phase=determine_edrr_phase(change)
        )

        # Save the updated requirement
        return self.requirement_repository.save_requirement(requirement)

    def delete_requirement(
        self, requirement_id: UUID, user_id: str, reason: str
    ) -> bool:
        """
        Delete a requirement.

        Args:
            requirement_id: The ID of the requirement to delete.
            user_id: The ID of the user deleting the requirement.
            reason: The reason for the deletion.

        Returns:
            True if the requirement was deleted, False otherwise.
        """
        # Get the requirement
        requirement = self.requirement_repository.get_requirement(requirement_id)
        if not requirement:
            return False

        # Create a change record
        change = RequirementChange(
            requirement_id=requirement.id,
            change_type=ChangeType.REMOVE,
            previous_state=requirement,
            created_by=user_id,
            reason=reason,
        )
        self.change_repository.save_change(change)

        # Notify about the proposed change
        self.notification_service.notify_change_proposed(change)

        # Evaluate the change using dialectical reasoning
        reasoning = self.dialectical_reasoner.evaluate_change(
            change, edrr_phase=determine_edrr_phase(change)
        )

        # Assess the impact of the change
        impact = self.dialectical_reasoner.assess_impact(
            change, edrr_phase=determine_edrr_phase(change)
        )

        # Delete the requirement
        return self.requirement_repository.delete_requirement(requirement_id)

    def approve_change(
        self, change_id: UUID, user_id: str
    ) -> Optional[RequirementChange]:
        """
        Approve a requirement change.

        Args:
            change_id: The ID of the change to approve.
            user_id: The ID of the user approving the change.

        Returns:
            The approved change if found, None otherwise.
        """
        # Get the change
        change = self.change_repository.get_change(change_id)
        if not change:
            return None

        # Update the change
        change.approved = True
        change.approved_at = datetime.now()
        change.approved_by = user_id

        # Save the change
        saved_change = self.change_repository.save_change(change)

        # Notify about the approved change
        self.notification_service.notify_change_approved(saved_change)

        return saved_change

    def reject_change(
        self, change_id: UUID, user_id: str, comment: str
    ) -> Optional[RequirementChange]:
        """
        Reject a requirement change.

        Args:
            change_id: The ID of the change to reject.
            user_id: The ID of the user rejecting the change.
            comment: A comment explaining the rejection.

        Returns:
            The rejected change if found, None otherwise.
        """
        # Get the change
        change = self.change_repository.get_change(change_id)
        if not change:
            return None

        # Update the change
        change.approved = False
        change.comments.append(f"{user_id}: {comment}")

        # Save the change
        saved_change = self.change_repository.save_change(change)

        # Notify about the rejected change
        self.notification_service.notify_change_rejected(saved_change)

        return saved_change

    def get_changes_for_requirement(
        self, requirement_id: UUID
    ) -> List[RequirementChange]:
        """
        Get changes for a requirement.

        Args:
            requirement_id: The ID of the requirement.

        Returns:
            A list of changes for the requirement.
        """
        return self.change_repository.get_changes_for_requirement(requirement_id)
