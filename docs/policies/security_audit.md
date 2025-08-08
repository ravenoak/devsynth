---
title: "Security Audit Procedure"
status: "draft"
---

# Security Audit Procedure

DevSynth enforces security policies through automated audits that run
static analysis and dependency vulnerability checks. These audits help
ensure code quality and supply chain safety.

## Tools

- **Bandit** – scans the `src` tree for common security issues.
- **Safety** – checks project dependencies for known vulnerabilities.

## Running Locally

Run the bundled script to execute both tools:

```bash
poetry run python scripts/dependency_safety_check.py
```

To skip checks or update dependencies first:

```bash
poetry run python scripts/dependency_safety_check.py --skip-bandit --skip-safety
poetry run python scripts/dependency_safety_check.py --update
```

## Continuous Integration

`bandit` and `safety` run in CI via disabled workflows
[`dependency_check.yml`](../../.github/workflows.disabled/dependency_check.yml)
and
[`static_analysis.yml`](../../.github/workflows.disabled/static_analysis.yml).
These workflows install dependencies with Poetry and execute the
`scripts/dependency_safety_check.py` utility on pull requests and pushes to
`main` when enabled.

## Logging

The audit functions emit log messages through the DevSynth logging
framework. Set `DEVSYNTH_AUDIT_LOG_ENABLED=0` to disable audit logging.
