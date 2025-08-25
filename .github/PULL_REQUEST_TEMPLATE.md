# Pull Request

Thank you for contributing to DevSynth!

Please fill out the checklist below to help us keep the repository healthy and aligned with our standards.

## Summary
- What does this PR change?
- Why is it needed?
- Linked issues/epics (if any):

## Checklist
- [ ] I ran quick sanity checks locally:
  - [ ] poetry run pytest --collect-only -q
  - [ ] poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel (or --smoke for plugin isolation)
- [ ] I verified style and typing (as applicable):
  - [ ] poetry run black --check . && poetry run isort --check-only .
  - [ ] poetry run flake8 src/ tests/
  - [ ] poetry run mypy src/devsynth (or added/updated TODOs when relaxing strictness as per .junie/guidelines.md)
- [ ] I followed .junie/guidelines.md and the priorities in docs/plan.md.
- [ ] I updated docs as needed and verified links if touched.
- [ ] I confirmed no secrets or credentials were added.

## Tasks Checklist Alignment (docs/tasks.md)
- [ ] If this PR completes any item(s) in docs/tasks.md, I updated the checklist:
  - Marked the task(s) as [x].
  - Added a short completion note with date and context.
  - Ensured changes reflect the improvement plan in docs/plan.md.

## Testing Notes
- What scenarios were tested? Any resource-gated tests involved?
- If adding tests, ensure exactly one speed marker per test function (fast|medium|slow).

## Breaking Changes
- [ ] None
- [ ] Describe breaking changes (if any) and migration notes:

## Additional Context
- Environment (OS, Python, Poetry):
- Any follow-ups or TODOs:
