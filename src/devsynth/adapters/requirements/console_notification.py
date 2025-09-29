"""Console notification adapter for requirements management."""

from __future__ import annotations

import logging

from devsynth.application.requirements.models import (
    ChangeNotificationPayload,
    ImpactNotificationPayload,
)
from devsynth.ports.requirement_port import NotificationPort


class ConsoleNotificationAdapter(NotificationPort):
    """Console implementation of the notification port."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the console notification adapter.

        Args:
            logger: Logger to use for notifications. If ``None``,
                a new logger will be created.
        """
        self.logger = logger or logging.getLogger(__name__)

    def _log_change(self, payload: ChangeNotificationPayload) -> None:
        change = payload.change
        prefix = payload.event.value.upper()
        self.logger.info("NOTIFICATION: Change %s - ID: %s", prefix, change.id)
        self.logger.info("  Type: %s", change.change_type.value)
        self.logger.info("  Requirement ID: %s", change.requirement_id)
        self.logger.info("  Proposed by: %s", change.created_by)
        if payload.audit.reason:
            self.logger.info("  Reason: %s", payload.audit.reason)

        if change.change_type.value == "add" and change.new_state:
            self.logger.info("  New requirement: %s", change.new_state.title)
        elif change.change_type.value == "remove" and change.previous_state:
            self.logger.info("  Removing requirement: %s", change.previous_state.title)
        elif change.change_type.value == "modify":
            if change.previous_state and change.new_state:
                self.logger.info(
                    "  Modifying requirement: %s -> %s",
                    change.previous_state.title,
                    change.new_state.title,
                )

    def notify_change_proposed(self, payload: ChangeNotificationPayload) -> None:
        """
        Notify that a change has been proposed.

        Args:
            payload: The proposed change payload.
        """
        self._log_change(payload)

    def notify_change_approved(self, payload: ChangeNotificationPayload) -> None:
        """
        Notify that a change has been approved.

        Args:
            payload: The approved change payload.
        """
        change = payload.change
        self._log_change(payload)
        self.logger.info("  Approved by: %s", change.approved_by)
        self.logger.info("  Approved at: %s", change.approved_at)

    def notify_change_rejected(self, payload: ChangeNotificationPayload) -> None:
        """
        Notify that a change has been rejected.

        Args:
            payload: The rejected change payload.
        """
        change = payload.change
        self._log_change(payload)
        self.logger.info("  Comments: %s", change.comments)

    def notify_impact_assessment_completed(
        self, payload: ImpactNotificationPayload
    ) -> None:
        """
        Notify that an impact assessment has been completed.

        Args:
            payload: The completed impact assessment payload.
        """
        assessment = payload.assessment
        self.logger.info(
            "NOTIFICATION: Impact assessment completed - ID: %s", assessment.id
        )
        self.logger.info("  Change ID: %s", assessment.change_id)
        self.logger.info("  Risk level: %s", assessment.risk_level)
        self.logger.info("  Estimated effort: %s", assessment.estimated_effort)
        self.logger.info(
            "  Affected requirements: %s", len(assessment.affected_requirements)
        )
        self.logger.info("  Affected components: %s", assessment.affected_components)
