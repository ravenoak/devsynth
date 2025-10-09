"""Additional CLI commands not part of primary groups."""

from __future__ import annotations

import os

from ..registry import register

_MINIMAL_CLI = os.environ.get("DEVSYNTH_CLI_MINIMAL") == "1"

from .run_tests_cmd import run_tests_cmd

register("run-tests", run_tests_cmd)

__all__ = ["run_tests_cmd"]


if not _MINIMAL_CLI:
    from .align_cmd import align_cmd
    from .atomic_rewrite_cmd import atomic_rewrite_cmd
    from .completion_cmd import completion_cmd
    from .edrr_cycle_cmd import edrr_cycle_cmd
    from .init_cmd import init_cmd
    from .mvuu_dashboard_cmd import mvuu_dashboard_cmd
    from .reprioritize_issues_cmd import reprioritize_issues_cmd
    from .security_audit_cmd import security_audit_cmd

    # from .testing_cmd import testing_cmd  # Temporarily disabled - CLI foundation ready

    register("align", align_cmd)
    register("completion", completion_cmd)
    register("init", init_cmd)
    # register("testing", testing_cmd)  # Temporarily disabled - CLI foundation ready
    register("edrr-cycle", edrr_cycle_cmd)
    register("security-audit", security_audit_cmd)
    register("reprioritize-issues", reprioritize_issues_cmd)
    register("atomic-rewrite", atomic_rewrite_cmd)
    # Optional MVUU dashboard launcher (kept lightweight for smoke tests)
    register("mvuu-dashboard", mvuu_dashboard_cmd)

    __all__ += [
        "align_cmd",
        "completion_cmd",
        "init_cmd",
        # "testing_cmd",  # Temporarily disabled - CLI foundation ready
        "edrr_cycle_cmd",
        "security_audit_cmd",
        "reprioritize_issues_cmd",
        "mvuu_dashboard_cmd",
        "atomic_rewrite_cmd",
    ]
