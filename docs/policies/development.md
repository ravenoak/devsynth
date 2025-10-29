---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:
- policy
title: Development Policy
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Development Policy
</div>

# Development Policy

This policy defines best practices for implementation, code quality, collaboration, and security in DevSynth.

## Key Practices

- Follow the [Contributing Guide](../developer_guides/contributing.md) for branching, PRs, and commit conventions.
- Reference requirement IDs in commit messages, PRs, and code/test docstrings for traceability.
- Adhere to the [Code Style Guide](../developer_guides/code_style.md) and use automated tools (Black, isort, flake8).
- Maintain strict type safety with mypy; all code must pass `mypy --strict` checking.
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
## Implementation Status

This feature is **implemented**.
