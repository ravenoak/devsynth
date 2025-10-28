"""
Prompt Efficacy Tracker module.

This module defines the PromptEfficacyTracker class for tracking and optimizing
prompt efficacy over time.
"""

import json
import os
import statistics
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class PromptEfficacyTracker:
    """
    Tracks and analyzes the efficacy of prompt templates.

    This class provides methods for tracking prompt usage, recording outcomes,
    and generating statistics and recommendations for prompt optimization.
    """

    def __init__(self, storage_path: str | None = None):
        """
        Initialize the prompt efficacy tracker.

        Args:
            storage_path: Path to store efficacy data (defaults to .devsynth/prompts/efficacy)
        """
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), ".devsynth", "prompts", "efficacy"
        )
        self.usage_data: dict[str, dict[str, list[dict[str, Any]]]] = {}

        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Load any existing efficacy data
        self._load_data()

        logger.info(
            f"Prompt efficacy tracker initialized with storage path: {self.storage_path}"
        )

    def track_usage(self, template_name: str, version_id: str) -> str:
        """
        Track the usage of a prompt template.

        Args:
            template_name: The name of the template
            version_id: The ID of the template version

        Returns:
            A unique tracking ID for this usage
        """
        tracking_id = str(uuid.uuid4())

        # Initialize data structures if needed
        if template_name not in self.usage_data:
            self.usage_data[template_name] = {}

        if version_id not in self.usage_data[template_name]:
            self.usage_data[template_name][version_id] = []

        # Record the usage
        usage = {
            "tracking_id": tracking_id,
            "timestamp": datetime.now().isoformat(),
            "outcome": None,  # Will be set later
            "metrics": {},
        }

        self.usage_data[template_name][version_id].append(usage)
        self._save_data()

        logger.debug(
            f"Tracked usage of template '{template_name}' version '{version_id}' with ID {tracking_id}"
        )
        return tracking_id

    def record_outcome(
        self,
        tracking_id: str,
        success: bool,
        metrics: dict[str, Any] | None = None,
        feedback: str | None = None,
    ) -> bool:
        """
        Record the outcome of a prompt usage.

        Args:
            tracking_id: The tracking ID returned from track_usage
            success: Whether the prompt usage was successful
            metrics: Optional metrics for the usage (e.g., response time, token count)
            feedback: Optional feedback on the prompt usage

        Returns:
            True if the outcome was recorded, False if the tracking ID wasn't found
        """
        # Find the usage record
        for template_name, versions in self.usage_data.items():
            for version_id, usages in versions.items():
                for usage in usages:
                    if usage["tracking_id"] == tracking_id:
                        # Record the outcome
                        usage["outcome"] = {
                            "success": success,
                            "timestamp": datetime.now().isoformat(),
                            "metrics": metrics or {},
                            "feedback": feedback,
                        }

                        self._save_data()
                        logger.debug(
                            f"Recorded outcome for tracking ID {tracking_id}: success={success}"
                        )
                        return True

        logger.warning(f"No usage found for tracking ID {tracking_id}")
        return False

    def get_efficacy_metrics(
        self, template_name: str, version_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get efficacy metrics for a prompt template.

        Args:
            template_name: The name of the template
            version_id: Optional ID of the version to get metrics for (all versions if not specified)

        Returns:
            A dictionary of metrics
        """
        if template_name not in self.usage_data:
            return {"error": f"No data for template '{template_name}'"}

        versions = self.usage_data[template_name]

        if version_id:
            # Get metrics for a specific version
            if version_id not in versions:
                return {
                    "error": f"No data for version '{version_id}' of template '{template_name}'"
                }

            return self._calculate_metrics_for_version(
                template_name, version_id, versions[version_id]
            )
        else:
            # Get metrics for all versions
            all_metrics = {}
            for vid, usages in versions.items():
                all_metrics[vid] = self._calculate_metrics_for_version(
                    template_name, vid, usages
                )

            # Add comparison metrics
            if len(all_metrics) > 1:
                all_metrics["comparison"] = self._compare_versions(all_metrics)

            return all_metrics

    def get_optimization_recommendations(
        self, template_name: str
    ) -> list[dict[str, Any]]:
        """
        Get recommendations for optimizing a prompt template.

        Args:
            template_name: The name of the template

        Returns:
            A list of recommendation dictionaries
        """
        if template_name not in self.usage_data:
            return []

        metrics = self.get_efficacy_metrics(template_name)
        recommendations = []

        # Check if we have version comparison data
        if "comparison" in metrics:
            best_version = metrics["comparison"].get("best_version")
            if best_version:
                recommendations.append(
                    {
                        "type": "version_selection",
                        "message": f"Version {best_version} has the highest success rate",
                        "action": f"Consider using version {best_version} as the default",
                    }
                )

        # Check for versions with low success rates
        for version_id, version_metrics in metrics.items():
            if version_id == "comparison":
                continue

            success_rate = version_metrics.get("success_rate", 0)
            if success_rate < 0.7 and version_metrics.get("total_usages", 0) > 5:
                recommendations.append(
                    {
                        "type": "version_improvement",
                        "message": f"Version {version_id} has a low success rate ({success_rate:.2f})",
                        "action": "Consider revising this version or creating a new one",
                    }
                )

        return recommendations

    def _calculate_metrics_for_version(
        self, template_name: str, version_id: str, usages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate metrics for a specific version of a template."""
        total_usages = len(usages)
        usages_with_outcome = [u for u in usages if u.get("outcome") is not None]
        successful_usages = [
            u for u in usages_with_outcome if u.get("outcome", {}).get("success", False)
        ]

        metrics = {
            "template_name": template_name,
            "version_id": version_id,
            "total_usages": total_usages,
            "usages_with_outcome": len(usages_with_outcome),
            "successful_usages": len(successful_usages),
            "success_rate": (
                len(successful_usages) / len(usages_with_outcome)
                if usages_with_outcome
                else 0
            ),
            "first_usage": usages[0]["timestamp"] if usages else None,
            "last_usage": usages[-1]["timestamp"] if usages else None,
        }

        # Calculate additional metrics if available
        response_times = []
        token_counts = []

        for usage in usages_with_outcome:
            outcome = usage.get("outcome", {})
            metrics_data = outcome.get("metrics", {})

            if "response_time" in metrics_data:
                response_times.append(metrics_data["response_time"])

            if "token_count" in metrics_data:
                token_counts.append(metrics_data["token_count"])

        if response_times:
            metrics["avg_response_time"] = statistics.mean(response_times)
            metrics["min_response_time"] = min(response_times)
            metrics["max_response_time"] = max(response_times)

        if token_counts:
            metrics["avg_token_count"] = statistics.mean(token_counts)
            metrics["min_token_count"] = min(token_counts)
            metrics["max_token_count"] = max(token_counts)

        return metrics

    def _compare_versions(
        self, version_metrics: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Compare metrics across versions."""
        # Find the version with the highest success rate
        best_version = None
        best_success_rate = -1

        for version_id, metrics in version_metrics.items():
            success_rate = metrics.get("success_rate", 0)
            if (
                success_rate > best_success_rate
                and metrics.get("usages_with_outcome", 0) >= 5
            ):
                best_success_rate = success_rate
                best_version = version_id

        return {
            "best_version": best_version,
            "best_success_rate": best_success_rate,
            "version_count": len(version_metrics),
        }

    def _load_data(self) -> None:
        """Load efficacy data from the storage path."""
        data_file = os.path.join(self.storage_path, "efficacy_data.json")
        if os.path.exists(data_file):
            try:
                with open(data_file) as f:
                    self.usage_data = json.load(f)
                logger.debug("Loaded prompt efficacy data")
            except Exception as e:
                logger.error(f"Error loading efficacy data: {str(e)}")
                self.usage_data = {}
        else:
            self.usage_data = {}

    def _save_data(self) -> None:
        """Save efficacy data to the storage path."""
        data_file = os.path.join(self.storage_path, "efficacy_data.json")
        try:
            with open(data_file, "w") as f:
                json.dump(self.usage_data, f, indent=2)
            logger.debug("Saved prompt efficacy data")
        except Exception as e:
            logger.error(f"Error saving efficacy data: {str(e)}")
