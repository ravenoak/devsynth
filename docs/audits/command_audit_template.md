# Command Audit Log Template

Use this template to capture evidence for execution-dependent tasks in docs/tasks.md §7 and docs/plan.md §3 and §7. Keep entries concise, link artifacts, and prefer reproducibility.

- Command:
- Runner: <local|CI job name>
- Environment:
  - Python:
  - OS/Arch:
  - DEVSYNTH_PROVIDER:
  - DEVSYNTH_OFFLINE:
  - PYTEST_DISABLE_PLUGIN_AUTOLOAD:
  - Extras installed: <tests|retrieval|chromadb|api|...>
- Start time:
- End time:
- Duration (s):
- Exit code:
- Working directory:
- Artifacts:
  - Primary: <path(s) under test_reports/ or uploaded artifact names>
  - Marker report (if applicable): test_reports/test_markers_report.json
  - Timing (if applicable): test_reports/smoke_fast_timing.txt
- Key output excerpt (paste short snippet or attach path):
- Notes/Observations:
  -
  -
- Follow-ups:
  -
  -
