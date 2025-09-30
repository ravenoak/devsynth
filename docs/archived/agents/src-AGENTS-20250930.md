# AGENTS.md

## Project Snapshot

**What lives in this directory?**
This directory holds DevSynth source code.

## Setup

**How do I prepare to hack on sources?**
Follow the repository setup from the root AGENTS and run commands through `poetry run`.

## Testing

**How do I verify changes?**
Run commands iteratively until they pass:
```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<fast|medium|slow>
```

## Conventions

**What coding conventions apply?**
- Follow the specification-first BDD workflow: draft specs in `../docs/specifications/` and failing features in `../tests/behavior/features/` before writing code.
- Adhere to the [Security Policy](../docs/policies/security.md), the [Dialectical Audit Policy](../docs/policies/dialectical_audit.md), and all documents under `../docs/policies/`; resolve `dialectical_audit.log`.
- Keep commit messages Conventional, invoke `make_pr` with a clear title and test summary, and update AGENTS files when workflows evolve.
- Use system time when recording the current date or datetime.

## Further Reading

**Where are detailed API and style guides?**
See `../docs/api_reference.md` and other references under `../docs/`.

## AGENTS.md Compliance

**What is the scope?**
These instructions apply to `src/` and its subdirectories. Nested AGENTS files override these instructions.
