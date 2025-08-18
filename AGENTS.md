# AGENTS

DevSynth uses a specification-first BDD workflow and starts every task with the Socratic checklist:

- What is the problem?
- What proofs confirm the solution?

Key policies:
- [Dialectical Audit Policy](docs/policies/dialectical_audit.md)
- [Documentation Policies](docs/policies/documentation_policies.md)

Directory-specific instructions:
- [src/AGENTS.md](src/AGENTS.md) – source code
- [docs/AGENTS.md](docs/AGENTS.md) – documentation

Run the environment provisioning script before development, execute commands through `poetry run`, and complete these pre-PR checks:

```
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<cat>
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
```
