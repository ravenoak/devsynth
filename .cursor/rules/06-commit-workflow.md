---
description: Conventional Commits standard and PR workflow
globs:
  - ".git/**/*"
  - ".github/**/*"
alwaysApply: false
---

# DevSynth Commit & PR Workflow

## Conventional Commits

**All commits must follow** [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): brief summary (max 50 chars)

Detailed explanation of what changed and why (wrap at 72 chars).

For significant changes, include dialectical analysis:
- Thesis: Original approach
- Antithesis: Problem identified  
- Synthesis: New solution

Closes #123
ReqID: FR-01, FR-02
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code restructuring without behavior change
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes
- `perf`: Performance improvements
- `style`: Code style/formatting

### Scopes

Common scopes:
- `cli`: CLI commands
- `memory`: Memory system
- `api`: API server
- `webui`: Web interface
- `gui`: GUI interface
- `agent`: Agent system
- `security`: Security features
- `docs`: Documentation
- `tests`: Test infrastructure

### Examples

```
feat(cli): add --offline mode for local model providers

Implements offline operation using transformers library for local
inference when network unavailable or --offline flag specified.

- Thesis: Always use cloud API for LLM calls
- Antithesis: Need offline capability for air-gapped environments
- Synthesis: Detect network/flag and fall back to local transformers

ReqID: FR-42
Closes #156
```

```
fix(memory): handle TinyDB TypeError during batch insert

Fixed TypeError when inserting multiple items simultaneously by
ensuring proper serialization of MemoryItem objects.

Closes #234
```

```
test(unit): add property tests for memory system invariants

Added hypothesis-based property tests to verify memory operations
maintain consistency under arbitrary inputs.

ReqID: NFR-08
```

## Pre-Commit Hooks

Install and maintain hooks:

```bash
# Install hooks
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg

# Update hooks
poetry run pre-commit autoupdate

# Run manually
poetry run pre-commit run --all-files
```

### Hook Behavior

The commit-msg hook enforces Conventional Commits format:
- Allows: Standard types with scope
- Allows: Merge commits
- Allows: WIP: prefix for local work
- Rejects: Non-conforming messages

## Pre-Commit Checklist

Before committing:

1. ✅ Code formatted: `poetry run black .`
2. ✅ Imports sorted: `poetry run isort .`
3. ✅ No lint errors: `poetry run flake8 src/ tests/`
4. ✅ Tests pass: `poetry run devsynth run-tests --speed=fast`
5. ✅ Markers verified: `poetry run python scripts/verify_test_markers.py --changed`
6. ✅ Audit resolved: `poetry run python scripts/dialectical_audit.py`
7. ✅ Hooks pass: `poetry run pre-commit run --files <changed>`

## Pull Request Workflow

### Creating PRs

1. Ensure fork is up to date with main
2. Run full pre-commit checklist
3. Push changes to feature branch
4. Create PR using template (`.github/pull_request_template.md`)
5. Link to issues via GitHub's "Linked issues" panel (required)
6. Reference `docs/tasks.md` items if applicable

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Problem Statement
What problem does this solve? (Socratic: What is the problem?)

## Solution
How does this solve it? (Socratic: What proofs confirm?)

## Dialectical Analysis
For significant changes:
- **Thesis**: Original approach
- **Antithesis**: Problem identified
- **Synthesis**: New solution

## Testing Evidence
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] BDD scenarios pass
- [ ] Manual testing completed

## Checklist
- [ ] Specification created in `docs/specifications/`
- [ ] BDD feature created with failing test
- [ ] Code follows style guide
- [ ] Tests include speed markers
- [ ] Documentation updated
- [ ] `dialectical_audit.log` resolved
- [ ] Conventional commit messages used

## Related
- Closes #<issue>
- ReqID: FR-XX, NFR-XX
- Related to `docs/tasks.md` item X.X
```

## Issue Workflow

### Creating Issues

Location: `issues/` (in-repo tracker)

Required elements:
- Clear title
- Problem description
- Acceptance criteria
- Socratic notes
- Dialectical notes (for significant changes)
- Labels: type, priority, status, area

### Issue Labels

**Type:**
- `type/bug`: Bug fix
- `type/feat`: New feature
- `type/docs`: Documentation
- `type/test`: Testing
- `type/chore`: Maintenance

**Priority:**
- `P0`: Urgent
- `P1`: Soon
- `P2`: Normal
- `P3`: Nice-to-have

**Status:**
- `status/triage`: Needs assessment
- `status/in-progress`: Active work
- `status/review`: In PR review
- `status/blocked`: Blocked
- `status/done`: Completed

**Area:**
- `area/cli`
- `area/testing`
- `area/providers`
- `area/docs`
- etc.

### Issue Template

```markdown
---
title: "<Issue Title>"
labels: ["type/feat", "P2", "status/triage"]
---

## Problem (Socratic: What is the problem?)
Clear description of the need or issue.

## Acceptance Criteria (Socratic: What proofs confirm?)
1. Observable behavior 1
2. Observable behavior 2

## Dialectical Notes
- **Thesis**: Current/assumed approach
- **Antithesis**: Challenge or alternative
- **Synthesis**: Proposed resolution

## Related
- ReqID: FR-XX
- Related issues: #XX
- Specification: `docs/specifications/<name>.md`
```

## Git Branch Strategy

- `main`: Production-ready code
- `feature/<name>`: Feature development
- `fix/<name>`: Bug fixes
- `docs/<name>`: Documentation updates

## Commit Hygiene

### Good Commits

- Atomic: One logical change per commit
- Descriptive: Clear what and why
- Tested: All tests pass
- Clean: No debug code, commented code

### Bad Commits (avoid)

- Mixing unrelated changes
- Vague messages ("fix stuff", "update")
- Breaking tests
- Including debug/commented code

## Rebase Guidelines

Keep history clean:
```bash
# Update feature branch
git fetch origin
git rebase origin/main

# Interactive rebase to clean up
git rebase -i HEAD~5
```

Never force push to shared branches.

## Review Process

1. PR submitted with complete description
2. Automated checks run (CI)
3. Code review by team
4. Address feedback
5. Approval and merge

## Merge Strategy

- Squash and merge for feature branches
- Preserve commit history for important features
- Delete branch after merge

