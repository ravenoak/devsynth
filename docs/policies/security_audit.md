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

Use the bundled script, which delegates to
`src/devsynth/security/audit.py`:

```bash
poetry run python scripts/security_audit.py
```

To skip checks:

```bash
poetry run python scripts/security_audit.py --skip-bandit --skip-safety
```

## Continuous Integration

`bandit` and `safety` run in CI via a disabled workflow
[`.github/workflows/ci.yml.disabled`](../../.github/workflows/ci.yml.disabled).
The workflow installs dependencies with Poetry and executes the bundled
`scripts/security_audit.py` utility on pull requests and pushes to
`main` when enabled.

## Logging

The audit functions emit log messages through the DevSynth logging
framework. Set `DEVSYNTH_AUDIT_LOG_ENABLED=0` to disable audit logging.
