"""
Command modules for the CLI application.
"""

# Import the command functions to make them available from this package
from .inspect_code_cmd import inspect_code_cmd
from .inspect_config_cmd import inspect_config_cmd
from .doctor_cmd import doctor_cmd
from .edrr_cycle_cmd import edrr_cycle_cmd
from .align_cmd import align_cmd
from .validate_manifest_cmd import validate_manifest_cmd
from .validate_metadata_cmd import validate_metadata_cmd
from .alignment_metrics_cmd import alignment_metrics_cmd
from .test_metrics_cmd import test_metrics_cmd
from .generate_docs_cmd import generate_docs_cmd
from .analyze_manifest_cmd import analyze_manifest_cmd

__all__ = [
    "inspect_code_cmd",
    "inspect_config_cmd",
    "doctor_cmd",
    "edrr_cycle_cmd",
    "align_cmd",
    "validate_manifest_cmd",
    "validate_metadata_cmd",
    "alignment_metrics_cmd",
    "test_metrics_cmd",
    "generate_docs_cmd",
    "analyze_manifest_cmd",
]
