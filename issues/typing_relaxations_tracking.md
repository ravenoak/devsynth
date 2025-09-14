# Typing Relaxations Tracking (toward 2025-10-01)

Purpose: Track modules listed under [tool.mypy.overrides] in pyproject.toml with relaxations or ignore flags, and plan restoration to strict mode by 2025-10-01 as required by docs/plan.md and docs/tasks.md Task 12.

How to use this document:
- Run: poetry run python scripts/list_mypy_overrides.py
- Review diagnostics/mypy_overrides.json and identify owners for each module group.
- For each module, create a follow-up issue with a concrete checklist to remove overrides and restore strict typing.
- Update the table below with links and status.

| Module pattern | Current relaxations | Owner | Issue link | Target date | Status |
|---|---|---|---|---|---|
| devsynth.application.cli.commands.inspect_code_cmd | removed | TBD | [restore-strict-typing-inspect-code-cmd.md](restore-strict-typing-inspect-code-cmd.md) | 2025-10-01 | closed |
| devsynth.feature_markers | removed | TBD | [restore-strict-typing-feature-markers.md](restore-strict-typing-feature-markers.md) | 2025-10-01 | closed |
| devsynth.core.mvu.* | removed | TBD | [restore-strict-typing-core-mvu.md](restore-strict-typing-core-mvu.md) | 2025-10-01 | closed |
| devsynth.application.documentation.* | removed | TBD | [restore-strict-typing-application-documentation.md](restore-strict-typing-application-documentation.md) | 2025-10-01 | closed |
| devsynth.domain.models.requirement | removed | TBD | [restore-strict-typing-domain.md](restore-strict-typing-domain.md) | 2025-10-01 | closed |
| devsynth.application.performance | removed | TBD | [restore-strict-typing-application-performance.md](restore-strict-typing-application-performance.md) | 2025-10-01 | closed |
| devsynth.adapters.requirements.* | removed | TBD | [restore-strict-typing-adapters-requirements.md](restore-strict-typing-adapters-requirements.md) | 2025-10-01 | closed |
| devsynth.application.memory.adapters.* | removed | TBD | [restore-strict-typing-application-memory-adapters.md](restore-strict-typing-application-memory-adapters.md) | 2025-10-01 | closed |
| devsynth.exceptions | removed | TBD | [restore-strict-typing-exceptions.md](restore-strict-typing-exceptions.md) | 2025-10-01 | closed |
| devsynth.testing.* | removed | TBD | [restore-strict-typing-testing.md](restore-strict-typing-testing.md) | 2025-10-01 | closed |
| devsynth.methodology.sprint | removed | TBD | [restore-strict-typing-methodology-sprint.md](restore-strict-typing-methodology-sprint.md) | 2025-10-01 | closed |
| devsynth.logger | removed | TBD | [restore-strict-typing-logger.md](restore-strict-typing-logger.md) | 2025-10-01 | closed |
| devsynth.methodology.* | removed | TBD | [restore-strict-typing-methodology.md](restore-strict-typing-methodology.md) | 2025-10-01 | closed |
| devsynth.application.edrr.* | ignore_errors=true | TBD | [restore-strict-typing-application-edrr.md](restore-strict-typing-application-edrr.md) | 2025-10-01 | open |

Notes:
- This table is seeded automatically from pyproject.toml relaxations as of 2025-09-02. Keep it updated as overrides are narrowed or removed.
- Add TODO comments in modules when touching code to remind about the strictness restoration deadline.
- 2025-09-10: Removed the mypy override for `devsynth.cli` after upgrading Typer to a typed release.
- 2025-09-14: Removed the mypy override for `devsynth.methodology.edrr.reasoning_loop` after adding type annotations.
- 2025-09-13: Removed the mypy override for `devsynth.adapters.*` after restoring type coverage.
- 2025-09-13: Attempted to remove the `devsynth.application.edrr.*` override, but `poetry run mypy src/devsynth/application/edrr`
  reported 430 errors; the ignore remains in place.
- 2025-09-14: Removed the mypy override for `devsynth.exceptions` after adding type hints.
- 2025-09-14: Added `-> None` annotations for exception constructors and typed `__cause__` attributes.
- 2025-09-14: Removed the mypy override for `devsynth.feature_markers` after annotating marker functions.
- 2025-09-14: Removed the mypy override for `devsynth.adapters.requirements.*` after adding type hints.
- 2025-09-15: Removed broad mypy override for `devsynth.domain.*`; current run reports 549 errors across 22 files.
- 2025-09-14: Removed the mypy override for `devsynth.domain.models.requirement`; domain typing now reports 617 errors across 26 files.
- 2025-09-14: Removed the mypy override for `devsynth.application.performance` after adding structured metrics types.
- 2025-09-14: Removed the mypy override for `devsynth.core.mvu.*` after restoring strict typing.
- 2025-09-14: Removed the mypy overrides for `devsynth.methodology.*` and `devsynth.methodology.sprint` after enforcing strict typing.
- 2025-09-14: Removed the mypy override for `devsynth.testing.*` after clarifying helper contracts.
- 2025-09-14: Verified `devsynth.cli` uses strict typing with no remaining `type: ignore` comments.
