# AGENTS.md

This directory holds DevSynth source code.

- Follow the specification-first BDD workflow: draft a specification in `../docs/specifications/` and add a failing BDD feature in `../tests/behavior/features/` before writing code.
- Implementations must follow the [Security Policy](../docs/policies/security.md) and the [Dialectical Audit Policy](../docs/policies/dialectical_audit.md).
- Verify changes with `poetry run pre-commit run --files <changed>` and `poetry run devsynth run-tests --speed=<cat>`.
