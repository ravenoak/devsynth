# AGENTS.md

This directory holds DevSynth source code.

- follow the specification-first BDD workflow: draft a specification in `../docs/specifications/` and add a failing BDD feature in `../tests/behavior/features/` before writing code;
- adhere to the [Security Policy](../docs/policies/security.md), the [Dialectical Audit Policy](../docs/policies/dialectical_audit.md), and all guidelines under `../docs/policies/`; resolve `dialectical_audit.log` before submitting a PR;
- verify changes with `poetry run pre-commit run --files <changed>` and `poetry run devsynth run-tests --speed=<cat>`;
- update this file when development practices evolve.
