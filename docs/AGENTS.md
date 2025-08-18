# AGENTS for docs/

- Follow the specification-first BDD workflow: add a spec in [specifications/](specifications/) and a failing feature in `../tests/behavior/features/` before updating docs.
- Apply the Socratic checklist: what is the problem and what proofs confirm the solution?
- Adhere to the [Dialectical Audit Policy](policies/dialectical_audit.md) and [Documentation Policies](policies/documentation_policies.md).
- Run the environment provisioning script and execute commands with `poetry run`.
- Before committing, run:

```text
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=fast
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
```
