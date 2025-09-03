# Typing Relaxations Tracking (toward 2025-10-01)

Purpose: Track modules listed under [tool.mypy.overrides] in pyproject.toml with relaxations or ignore flags, and plan restoration to strict mode by 2025-10-01 as required by docs/plan.md and docs/tasks.md Task 12.

How to use this document:
- Run: poetry run python scripts/list_mypy_overrides.py
- Review diagnostics/mypy_overrides.json and identify owners for each module group.
- For each module, create a follow-up issue with a concrete checklist to remove overrides and restore strict typing.
- Update the table below with links and status.

| Module pattern | Current relaxations | Owner | Issue link | Target date | Status |
|---|---|---|---|---|---|
| devsynth.application.cli.commands.inspect_code_cmd | disallow_untyped_defs=false, check_untyped_defs=false | TBD | TODO | 2025-10-01 | open |
| devsynth.methodology.edrr.reasoning_loop | disallow_untyped_defs=false, check_untyped_defs=false | TBD | TODO | 2025-10-01 | open |
| devsynth.feature_markers | disallow_untyped_defs=false, check_untyped_defs=false | TBD | TODO | 2025-10-01 | open |
| devsynth.core.mvu.* | disallow_untyped_defs=false, check_untyped_defs=false, ignore_missing_imports=true | TBD | TODO | 2025-10-01 | open |
| devsynth.application.documentation.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.domain.models.requirement | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.application.performance | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.adapters.requirements.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.application.memory.adapters.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.adapters.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.exceptions | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.testing.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.methodology.sprint | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.logger | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.methodology.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.domain.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |
| devsynth.application.edrr.* | ignore_errors=true | TBD | TODO | 2025-10-01 | open |

Notes:
- This table is seeded automatically from pyproject.toml relaxations as of 2025-09-02. Keep it updated as overrides are narrowed or removed.
- Add TODO comments in modules when touching code to remind about the strictness restoration deadline.
