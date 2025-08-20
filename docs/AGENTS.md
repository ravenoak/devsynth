# AGENTS.md

## Project Snapshot

**What lives in this directory?**
This directory hosts DevSynth documentation.

## Setup

**How do I prepare to edit docs?**
Follow the repository setup from the root AGENTS and run commands through `poetry run`.

## Testing

**How do I keep docs consistent?**
Run commands iteratively until they succeed:

```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<fast|medium|slow>
poetry run python scripts/verify_test_markers.py
```

CI runs this verification to ensure tests include appropriate speed markers.

## Conventions

**What guidelines shape documentation?**
- Capture new requirements in `specifications/` and pair them with failing features in `../tests/behavior/features/` before implementation.
- Honor [Documentation Policies](policies/documentation_policies.md), the [Dialectical Audit Policy](policies/dialectical_audit.md), and all files under `policies/`; resolve `dialectical_audit.log`.
- Treat `inspirational_docs/` as brainstorming only; papers in `external_research_papers/` may be cited.
- Keep commit messages Conventional and follow the root AGENTS for pull‑request steps.

## Further Reading

**Where can I find detailed style guides?**
See `policies/documentation_policies.md` and other references in this directory.

## AGENTS.md Compliance

**What is the scope here?**
These instructions apply to `docs/` and its subdirectories. Nested AGENTS files override these instructions.
