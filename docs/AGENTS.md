# AGENTS for docs/ (AI Contributors)

AI contributors editing `docs/` should:

- Follow the specification-first BDD workflow: add a spec in [specifications/](specifications/) and a failing feature in `../tests/behavior/features/` before updating docs.
- Apply the Socratic checklist: what is the problem and what proofs confirm the solution?
- Adhere to the [Dialectical Audit Policy](policies/dialectical_audit.md) and [Documentation Policies](policies/documentation_policies.md).
- Run the environment provisioning script and execute commands with `poetry run`.
- Complete the standard pre-PR checks listed in [../AGENTS.md](../AGENTS.md).
