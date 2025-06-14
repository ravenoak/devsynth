"""
Manifest Parser Module

This module provides a parser for EDRR manifests, which are used to drive the EDRR process.
It includes enhanced functionality for phase dependency tracking, execution progress monitoring,
and comprehensive logging and traceability.
"""
import json
import jsonschema
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from pathlib import Path

from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

logger = DevSynthLogger(__name__)

# Define the JSON schema for EDRR manifests
MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["id", "description", "phases"],
    "properties": {
        "id": {"type": "string"},
        "description": {"type": "string"},
        "metadata": {"type": "object"},
        "phases": {
            "type": "object",
            "required": ["expand", "differentiate", "refine", "retrospect"],
            "properties": {
                "expand": {
                    "type": "object",
                    "required": ["instructions"],
                    "properties": {
                        "instructions": {"type": "string"},
                        "templates": {"type": "array", "items": {"type": "string"}},
                        "resources": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"}
                    }
                },
                "differentiate": {
                    "type": "object",
                    "required": ["instructions"],
                    "properties": {
                        "instructions": {"type": "string"},
                        "templates": {"type": "array", "items": {"type": "string"}},
                        "resources": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"}
                    }
                },
                "refine": {
                    "type": "object",
                    "required": ["instructions"],
                    "properties": {
                        "instructions": {"type": "string"},
                        "templates": {"type": "array", "items": {"type": "string"}},
                        "resources": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"}
                    }
                },
                "retrospect": {
                    "type": "object",
                    "required": ["instructions"],
                    "properties": {
                        "instructions": {"type": "string"},
                        "templates": {"type": "array", "items": {"type": "string"}},
                        "resources": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"}
                    }
                }
            }
        }
    }
}

class ManifestParseError(DevSynthError):
    """Error raised when parsing an EDRR manifest fails."""
    pass

class ManifestParser:
    """
    Parser for EDRR manifests.

    This class provides methods for parsing, validating, and accessing EDRR manifests,
    which are used to drive the EDRR process. It includes enhanced functionality for
    phase dependency tracking, execution progress monitoring, and comprehensive logging
    and traceability.
    """

    def __init__(self):
        """Initialize the Manifest Parser."""
        self.manifest = None
        self.execution_trace = {}
        self.phase_dependencies = {
            Phase.DIFFERENTIATE: {Phase.EXPAND},
            Phase.REFINE: {Phase.DIFFERENTIATE},
            Phase.RETROSPECT: {Phase.REFINE}
        }
        self.phase_status = {}
        self.start_time = None
        logger.info("Manifest Parser initialized with enhanced traceability")

    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse an EDRR manifest from a file.

        Args:
            file_path: The path to the manifest file

        Returns:
            The parsed manifest as a dictionary

        Raises:
            ManifestParseError: If the file cannot be read or parsed
        """
        try:
            file_path = Path(file_path)
            with open(file_path, 'r') as f:
                manifest = json.load(f)

            # Validate the manifest
            self.validate(manifest)

            # Store the manifest
            self.manifest = manifest

            logger.info(f"Parsed EDRR manifest from file: {file_path}")
            return manifest
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to parse EDRR manifest from file: {e}")
            raise ManifestParseError(f"Failed to parse EDRR manifest from file: {e}")

    def parse_string(self, manifest_str: str) -> Dict[str, Any]:
        """
        Parse an EDRR manifest from a string.

        Args:
            manifest_str: The manifest as a JSON string

        Returns:
            The parsed manifest as a dictionary

        Raises:
            ManifestParseError: If the string cannot be parsed
        """
        try:
            manifest = json.loads(manifest_str)

            # Validate the manifest
            self.validate(manifest)

            # Store the manifest
            self.manifest = manifest

            logger.info("Parsed EDRR manifest from string")
            return manifest
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse EDRR manifest from string: {e}")
            raise ManifestParseError(f"Failed to parse EDRR manifest from string: {e}")

    def validate(self, manifest: Dict[str, Any]) -> None:
        """
        Validate an EDRR manifest against the schema.

        Args:
            manifest: The manifest to validate

        Raises:
            ManifestParseError: If the manifest is invalid
        """
        try:
            if hasattr(jsonschema, "validate"):
                jsonschema.validate(instance=manifest, schema=MANIFEST_SCHEMA)
            logger.info("Validated EDRR manifest")
        except Exception as e:
            logger.error(f"Invalid EDRR manifest: {e}")
            raise ManifestParseError(f"Invalid EDRR manifest: {e}")

    def get_phase_instructions(self, phase: Phase) -> str:
        """
        Get the instructions for a specific phase from the manifest.

        Args:
            phase: The phase to get instructions for

        Returns:
            The instructions for the specified phase

        Raises:
            ManifestParseError: If the manifest is not loaded or the phase is not found
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")

        phase_key = phase.value.lower()
        if phase_key not in self.manifest["phases"]:
            raise ManifestParseError(f"Phase '{phase_key}' not found in manifest")

        return self.manifest["phases"][phase_key]["instructions"]

    def get_phase_templates(self, phase: Phase) -> List[str]:
        """
        Get the templates for a specific phase from the manifest.

        Args:
            phase: The phase to get templates for

        Returns:
            The templates for the specified phase, or an empty list if none are specified

        Raises:
            ManifestParseError: If the manifest is not loaded or the phase is not found
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")

        phase_key = phase.value.lower()
        if phase_key not in self.manifest["phases"]:
            raise ManifestParseError(f"Phase '{phase_key}' not found in manifest")

        return self.manifest["phases"][phase_key].get("templates", [])

    def get_phase_resources(self, phase: Phase) -> List[str]:
        """
        Get the resources for a specific phase from the manifest.

        Args:
            phase: The phase to get resources for

        Returns:
            The resources for the specified phase, or an empty list if none are specified

        Raises:
            ManifestParseError: If the manifest is not loaded or the phase is not found
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")

        phase_key = phase.value.lower()
        if phase_key not in self.manifest["phases"]:
            raise ManifestParseError(f"Phase '{phase_key}' not found in manifest")

        return self.manifest["phases"][phase_key].get("resources", [])

    def get_manifest_id(self) -> str:
        """
        Get the ID of the manifest.

        Returns:
            The ID of the manifest

        Raises:
            ManifestParseError: If the manifest is not loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")

        return self.manifest["id"]

    def get_manifest_description(self) -> str:
        """
        Get the description of the manifest.

        Returns:
            The description of the manifest

        Raises:
            ManifestParseError: If the manifest is not loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")

        return self.manifest["description"]

    def get_manifest_metadata(self) -> Dict[str, Any]:
        """
        Get the metadata of the manifest.

        Returns:
            The metadata of the manifest, or an empty dictionary if none is specified

        Raises:
            ManifestParseError: If the manifest is not loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")

        return self.manifest.get("metadata", {})

    def start_execution(self) -> None:
        """
        Start tracking the execution of the EDRR process.
        
        This method initializes the execution trace and sets the start time.
        
        Raises:
            ManifestParseError: If no manifest is loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        self.start_time = time.time()
        self.execution_trace = {
            "manifest_id": self.get_manifest_id(),
            "start_time": datetime.now().isoformat(),
            "phases": {},
            "completed": False
        }
        
        # Initialize phase status
        for phase in Phase:
            phase_key = phase.value.lower()
            self.phase_status[phase] = {
                "status": "pending",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "dependencies_met": phase not in self.phase_dependencies
            }
        
        logger.info(f"Started execution tracking for manifest: {self.get_manifest_id()}")
    
    def check_phase_dependencies(self, phase: Phase) -> bool:
        """
        Check if all dependencies for a phase have been completed.
        
        Args:
            phase: The phase to check dependencies for
            
        Returns:
            True if all dependencies are met, False otherwise
            
        Raises:
            ManifestParseError: If no manifest is loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        # If the phase has no dependencies, return True
        if phase not in self.phase_dependencies:
            return True
        
        # Check if all dependencies have been completed
        for dependency in self.phase_dependencies[phase]:
            if self.phase_status.get(dependency, {}).get("status") != "completed":
                logger.warning(f"Dependency {dependency.value} not completed for phase {phase.value}")
                return False
        
        logger.info(f"All dependencies met for phase {phase.value}")
        return True
    
    def start_phase(self, phase: Phase) -> None:
        """
        Start tracking the execution of a phase.
        
        Args:
            phase: The phase to start tracking
            
        Raises:
            ManifestParseError: If no manifest is loaded or dependencies are not met
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        # Check if dependencies are met
        if not self.check_phase_dependencies(phase):
            raise ManifestParseError(f"Dependencies not met for phase {phase.value}")
        
        # Update phase status
        self.phase_status[phase] = {
            "status": "in_progress",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": None,
            "dependencies_met": True
        }
        
        # Update execution trace
        phase_key = phase.value.lower()
        self.execution_trace["phases"][phase_key] = {
            "status": "in_progress",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": None
        }
        
        logger.info(f"Started phase {phase.value}")
    
    def complete_phase(self, phase: Phase, result: Dict[str, Any] = None) -> None:
        """
        Complete tracking the execution of a phase.
        
        Args:
            phase: The phase to complete tracking
            result: Optional result data for the phase
            
        Raises:
            ManifestParseError: If no manifest is loaded or the phase is not in progress
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        # Check if the phase is in progress
        if self.phase_status.get(phase, {}).get("status") != "in_progress":
            raise ManifestParseError(f"Phase {phase.value} is not in progress")
        
        # Calculate duration
        start_time = datetime.fromisoformat(self.phase_status[phase]["start_time"])
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Update phase status
        self.phase_status[phase] = {
            "status": "completed",
            "start_time": self.phase_status[phase]["start_time"],
            "end_time": end_time.isoformat(),
            "duration": duration,
            "dependencies_met": True,
            "result": result
        }
        
        # Update execution trace
        phase_key = phase.value.lower()
        self.execution_trace["phases"][phase_key] = {
            "status": "completed",
            "start_time": self.phase_status[phase]["start_time"],
            "end_time": end_time.isoformat(),
            "duration": duration,
            "result": result
        }
        
        # Update dependencies for subsequent phases
        for next_phase, dependencies in self.phase_dependencies.items():
            if phase in dependencies:
                # Check if all dependencies are now met
                all_met = True
                for dependency in dependencies:
                    if self.phase_status.get(dependency, {}).get("status") != "completed":
                        all_met = False
                        break
                
                if all_met:
                    self.phase_status[next_phase]["dependencies_met"] = True
                    logger.info(f"Dependencies now met for phase {next_phase.value}")
        
        logger.info(f"Completed phase {phase.value} in {duration:.2f} seconds")
    
    def complete_execution(self) -> Dict[str, Any]:
        """
        Complete tracking the execution of the EDRR process.
        
        Returns:
            The execution trace
            
        Raises:
            ManifestParseError: If no manifest is loaded or not all phases are completed
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        # Check if all phases are completed
        all_completed = True
        for phase in Phase:
            if self.phase_status.get(phase, {}).get("status") != "completed":
                all_completed = False
                logger.warning(f"Phase {phase.value} not completed")
        
        # Calculate total duration
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        # Update execution trace
        self.execution_trace["end_time"] = datetime.now().isoformat()
        self.execution_trace["duration"] = total_duration
        self.execution_trace["completed"] = all_completed
        
        logger.info(f"Completed execution in {total_duration:.2f} seconds, all phases completed: {all_completed}")
        return self.execution_trace
    
    def get_execution_trace(self) -> Dict[str, Any]:
        """
        Get the current execution trace.
        
        Returns:
            The execution trace
            
        Raises:
            ManifestParseError: If no manifest is loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        return self.execution_trace
    
    def get_phase_status(self, phase: Phase) -> Dict[str, Any]:
        """
        Get the status of a phase.
        
        Args:
            phase: The phase to get the status for
            
        Returns:
            The status of the phase
            
        Raises:
            ManifestParseError: If no manifest is loaded
        """
        if not self.manifest:
            raise ManifestParseError("No manifest loaded")
        
        return self.phase_status.get(phase, {})
