# Development Policy

This policy defines best practices for implementation, code quality, collaboration, and security in DevSynth.

## Key Practices
- Follow the [Contributing Guide](../developer_guides/contributing.md) for branching, PRs, and commit conventions.
- Reference requirement IDs in commit messages, PRs, and code/test docstrings for traceability.
- Adhere to the [Code Style Guide](../developer_guides/code_style.md) and use automated tools (Black, isort, flake8).
- Use code review and approval before merging; at least one reviewer must check for policy compliance.
- Assign module ownership and document it in architecture docs or a CODEOWNERS file.
- Follow secure coding and ethical guidelines (see [Security Policy](security.md) if present).
- Update documentation and changelog with every significant code change.

## Artifacts
- Contribution Guide: `docs/developer_guides/contributing.md`
- Code Style Guide: `docs/developer_guides/code_style.md`
- Changelog: `CHANGELOG.md`
- CODEOWNERS: `CODEOWNERS` (if present)
- Security Policy: `docs/policies/security.md` (if present)

## References
- See [Design Policy](design.md) for architecture and interface contracts.
- See [Testing Policy](testing.md) for test requirements.

