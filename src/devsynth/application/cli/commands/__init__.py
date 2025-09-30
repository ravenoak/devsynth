"""Command modules for the CLI application."""

from __future__ import annotations

import os

from .run_tests_cmd import run_tests_cmd

__all__ = ["run_tests_cmd"]

if os.environ.get("DEVSYNTH_CLI_MINIMAL") != "1":
    from .align_cmd import align_cmd
    from .alignment_metrics_cmd import alignment_metrics_cmd
    from .analyze_manifest_cmd import analyze_manifest_cmd
    from .doctor_cmd import doctor_cmd
    from .edrr_cycle_cmd import edrr_cycle_cmd
    from .generate_docs_cmd import generate_docs_cmd
    from .ingest_cmd import ingest_cmd
    from .inspect_code_cmd import inspect_code_cmd
    from .inspect_config_cmd import inspect_config_cmd
    from .test_metrics_cmd import test_metrics_cmd
    from .validate_manifest_cmd import validate_manifest_cmd
    from .validate_metadata_cmd import validate_metadata_cmd

    __all__ += [
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
        "ingest_cmd",
    ]
