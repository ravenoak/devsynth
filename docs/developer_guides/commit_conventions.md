# Commit Message Conventions (Conventional Commits)

DevSynth enforces Conventional Commits in CI to improve traceability and automation.

Basic format:

<type>(optional scope)!: short summary

- Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- Scope is optional but recommended (e.g., `feat(cli): ...`)
- Use `!` before the colon to indicate a breaking change (and describe it in the body)
- Subject line maximums:
  - Soft limit: 72 characters (advised)
  - Hard limit: 100 characters (enforced)

Examples:
- feat(cli): add init command for project scaffolding
- fix(memory): resolve transaction rollback edge case
- docs: update provider configuration guide
- refactor(core)!: remove deprecated config loader

Notes:
- Body is optional; if present, wrap lines at ~100 characters.
- Reference issues when helpful (e.g., `Refs #123`).

CI integration:
- Workflow: .github/workflows/commit_message_lint.yml
- Linter: scripts/commit_linter.py
- PRs and pushes to main/develop/release branches must pass this check.

This policy aligns with the principles in .junie/guidelines.md and supports SDD/TDD/BDD by making change intent explicit.
