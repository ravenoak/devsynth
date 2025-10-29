---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-08-15"
status: published
tags:

- policy

title: Security Policy
version: "0.1.0a1"
review_cadence: quarterly
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Security Policy
</div>

# Security Policy

This policy outlines security design principles and operational guidelines for DevSynth.

## Review Cadence

This policy is reviewed quarterly by the DevSynth team to ensure it remains current and effective.

## Design Guidelines

- Apply the principle of least privilege for all agents and services.
- Encrypt sensitive data in transit and at rest where possible.
- Validate all environment variables and configuration inputs on startup.
- Keep dependencies patched and monitor vulnerability advisories.
- Document threat models and mitigations in the architecture docs.


## Operational Guidelines

- Enable or disable authentication, authorization and input sanitization via environment variables (`DEVSYNTH_AUTHENTICATION_ENABLED`, `DEVSYNTH_AUTHORIZATION_ENABLED`, `DEVSYNTH_SANITIZATION_ENABLED`).
- Encryption at rest for memory stores can be toggled with `DEVSYNTH_ENCRYPTION_AT_REST` and a base64 key provided via `DEVSYNTH_ENCRYPTION_KEY`.
- Encryption in transit can be enforced with `DEVSYNTH_ENCRYPTION_IN_TRANSIT`.
- TLS verification and certificates are configured using `DEVSYNTH_TLS_VERIFY`, `DEVSYNTH_TLS_CERT_FILE`, `DEVSYNTH_TLS_KEY_FILE` and `DEVSYNTH_TLS_CA_FILE`.
- Store API keys and secrets in environment variables or a secrets manager; never commit them to the repository.
- Deployment scripts verify `DEVSYNTH_ACCESS_TOKEN` is set and ensure any `.env` file has restrictive permissions and is not a symlink.
- Report suspected security issues or vulnerabilities through the issue tracker.
- Review security settings as part of routine cross‑cutting concern audits.
- Maintain logs for security relevant events and restrict access to them.


### Example Configuration

```bash
export DEVSYNTH_ENCRYPTION_AT_REST=true
export DEVSYNTH_ENCRYPTION_KEY="$(python -c 'from devsynth.security.encryption import generate_key; print(generate_key())')"
export DEVSYNTH_TLS_CERT_FILE=/path/to/cert.pem
export DEVSYNTH_TLS_KEY_FILE=/path/to/key.pem
export DEVSYNTH_TLS_CA_FILE=/path/to/ca.pem
export DEVSYNTH_ACCESS_TOKEN=my-secret-token
```

## Automated Audit Procedures and Enforcement

DevSynth automates routine security checks to prevent regressions:

- A GitHub Actions workflow can be manually dispatched to run Bandit static
  analysis and Safety dependency scans via pre-commit.
- The `policy_audit` script scans configuration and source files for hardcoded
  secrets or debug flags and is run as part of pre-commit checks:

  ```bash
  poetry run python scripts/policy_audit.py
  ```
- The `security-audit` CLI command validates required security configuration
  flags using `scripts/verify_security_policy.py` before performing dependency
  vulnerability scans and Bandit static analysis. Deployment pipelines must set
  `DEVSYNTH_PRE_DEPLOY_APPROVED=true` before invoking this command to enforce
  policy compliance prior to publishing artifacts.
- The command exits with a non‑zero status if any check fails, which blocks CI
  pipelines and deployment.
- Developers should run `devsynth security-audit` locally before committing
  changes to catch issues early.

### Audit Reporting

The `security-audit` command records the outcome of each check and can write a
machine-readable summary. Passing `--report <file>` generates a JSON document
with `bandit` and `safety` fields set to `passed`, `failed`, or `skipped`.
Deployment pipelines can archive this report for traceability.

```bash
DEVSYNTH_PRE_DEPLOY_APPROVED=true poetry run python scripts/security_audit.py
```


### Audit Checklist

1. Verify required security flags:
   `poetry run python scripts/verify_security_policy.py`.
2. Run the combined Bandit and Safety scan:
   `poetry run python scripts/security_audit.py --report security_audit.json`.
3. Review the generated report and address any failures.
4. Archive the report with release artifacts.


### Enforceable Audit Criteria

The following settings must be configured for deployments and are verified by
`scripts/verify_security_policy.py`:

- `DEVSYNTH_AUTHENTICATION_ENABLED` is set to `true`.
- `DEVSYNTH_AUTHORIZATION_ENABLED` is set to `true`.
- `DEVSYNTH_SANITIZATION_ENABLED` is set to `true`.
- `DEVSYNTH_ENCRYPTION_AT_REST` is set to `true`.
- `DEVSYNTH_ENCRYPTION_IN_TRANSIT` is set to `true`.
- `DEVSYNTH_TLS_VERIFY` is set to `true`.
- `DEVSYNTH_ACCESS_TOKEN` is non-empty.
- `DEVSYNTH_PRE_DEPLOY_APPROVED` is set to `true`.

Run `poetry run python scripts/verify_security_policy.py` to enforce these
criteria; the script exits with status `1` if any requirement is unmet.

## Periodic Security Reviews

Security policies and configurations are reviewed on a quarterly basis. The
`devsynth.security.review` module assists with scheduling and determining when a
review is due. For example:

```python
from datetime import date
from devsynth.security.review import is_review_due

if is_review_due(date(2024, 1, 1)):
    print("Security review required")
```

Teams should schedule a follow‑up review using `next_review_date` after each
assessment and ensure findings are tracked to completion.

### Review Process

1. At the start of each quarter, run the combined Bandit and Safety scan:
   `poetry run python scripts/security_audit.py --report security_audit.json`.
2. Record the generated report in the issue tracker. A sample failing report is
   provided at `examples/security_audit_failure_report.json`.
3. Use `devsynth.security.review.next_review_date` to schedule the next
   assessment.
4. Track all remediation tasks to closure before the next review cycle.

## Incident Response Procedures

The [Incident Response Runbook](../deployment/runbooks/incident_response.md)
describes manual steps for investigating and mitigating production issues.
Automated helpers are provided by `scripts/security_incident_response.py`:

```bash
# Collect logs and run a security audit
python scripts/security_incident_response.py --collect-logs --audit --output incident_$(date +%Y%m%d)
```

This script archives the `logs/` directory and executes the existing
`security-audit` command to aid in forensics.

## Vulnerability Management

Routine patching keeps dependencies up to date. Use
`scripts/vulnerability_management.py` to list outdated packages and optionally
apply updates:

```bash
# Show outdated dependencies
python scripts/vulnerability_management.py

# Apply available updates
python scripts/vulnerability_management.py --apply
```

These checks run in CI alongside `scripts/dependency_safety_check.py` to ensure
the project remains free of known vulnerabilities.

## Threat Model

The primary threats considered include:

- Unauthorized access to memory stores
- Interception of API traffic
- Misuse of agent or API credentials


Mitigations include encryption at rest, optional TLS for all network
communication, bearer token authentication for API and agent actions,
and routine dependency and static analysis checks in CI.
## Implementation Status
Security configuration flags and basic encryption utilities are implemented.
Automated audits and basic monitoring are provided via the
  `security-audit` command, available via `devsynth security-audit`.
Memory stores support encryption at rest and emit audit logs for store, retrieve,
and delete operations.
Runtime checks in [`src/devsynth/config/settings.py`](../../src/devsynth/config/settings.py)
validate encryption parameters on startup. The JSON file store implements
AES-based encryption in [`src/devsynth/application/memory/json_file_store.py`](../../src/devsynth/application/memory/json_file_store.py)
using helpers from [`src/devsynth/security/encryption.py`](../../src/devsynth/security/encryption.py).
Security incident response automation is provided via
`scripts/security_incident_response.py`. Dependency updates and vulnerability
checks are handled by `scripts/vulnerability_management.py` alongside the
existing safety and Bandit scans.
