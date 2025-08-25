"""
Console notification adapter for requirements management.
"""

import logging
from typing import Optional

from devsynth.domain.models.requirement import ImpactAssessment, RequirementChange
from devsynth.ports.requirement_port import NotificationPort


class ConsoleNotificationAdapter(NotificationPort):
    """
    Console implementation of the notification port.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the console notification adapter.

        Args:
            logger: Logger to use for notifications. If None, a new logger will be created.
        """
        self.logger = logger or logging.getLogger(__name__)

    def notify_change_proposed(self, change: RequirementChange) -> None:
        """
        Notify that a change has been proposed.

        Args:
            change: The proposed change.
        """
        self.logger.info(f"NOTIFICATION: Change proposed - ID: {change.id}")
        self.logger.info(f"  Type: {change.change_type.value}")
        self.logger.info(f"  Requirement ID: {change.requirement_id}")
        self.logger.info(f"  Proposed by: {change.created_by}")
        self.logger.info(f"  Reason: {change.reason}")

        if change.change_type.value == "add" and change.new_state:
            self.logger.info(f"  New requirement: {change.new_state.title}")
        elif change.change_type.value == "remove" and change.previous_state:
            self.logger.info(f"  Removing requirement: {change.previous_state.title}")
        elif change.change_type.value == "modify":
            if change.previous_state and change.new_state:
                self.logger.info(
                    f"  Modifying requirement: {change.previous_state.title} -> {change.new_state.title}"
                )

    def notify_change_approved(self, change: RequirementChange) -> None:
        """
        Notify that a change has been approved.

        Args:
            change: The approved change.
        """
        self.logger.info(f"NOTIFICATION: Change approved - ID: {change.id}")
        self.logger.info(f"  Type: {change.change_type.value}")
        self.logger.info(f"  Requirement ID: {change.requirement_id}")
        self.logger.info(f"  Approved by: {change.approved_by}")
        self.logger.info(f"  Approved at: {change.approved_at}")

    def notify_change_rejected(self, change: RequirementChange) -> None:
        """
        Notify that a change has been rejected.

        Args:
            change: The rejected change.
        """
        self.logger.info(f"NOTIFICATION: Change rejected - ID: {change.id}")
        self.logger.info(f"  Type: {change.change_type.value}")
        self.logger.info(f"  Requirement ID: {change.requirement_id}")
        self.logger.info(f"  Comments: {change.comments}")

    def notify_impact_assessment_completed(self, assessment: ImpactAssessment) -> None:
        """
        Notify that an impact assessment has been completed.

        Args:
            assessment: The completed impact assessment.
        """
        self.logger.info(
            f"NOTIFICATION: Impact assessment completed - ID: {assessment.id}"
        )
        self.logger.info(f"  Change ID: {assessment.change_id}")
        self.logger.info(f"  Risk level: {assessment.risk_level}")
        self.logger.info(f"  Estimated effort: {assessment.estimated_effort}")
        self.logger.info(
            f"  Affected requirements: {len(assessment.affected_requirements)}"
        )
        self.logger.info(f"  Affected components: {assessment.affected_components}")
