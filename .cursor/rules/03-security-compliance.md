---
description: Security policies and dialectical audit compliance
globs:
  - "src/**/*"
  - "scripts/**/*"
  - "docs/policies/**/*"
alwaysApply: false
---

# DevSynth Security & Compliance

## Security Policy

Follow `docs/policies/security.md` principles:

- Apply principle of least privilege
- Encrypt sensitive data in transit and at rest
- Validate all environment variables and inputs
- Keep dependencies patched
- Document threat models and mitigations

## Security Configuration

### Required Flags (Deployment)

```bash
export DEVSYNTH_AUTHENTICATION_ENABLED=true
export DEVSYNTH_AUTHORIZATION_ENABLED=true
export DEVSYNTH_SANITIZATION_ENABLED=true
export DEVSYNTH_ENCRYPTION_AT_REST=true
export DEVSYNTH_ENCRYPTION_IN_TRANSIT=true
export DEVSYNTH_TLS_VERIFY=true
export DEVSYNTH_ACCESS_TOKEN=<non-empty>
export DEVSYNTH_PRE_DEPLOY_APPROVED=true
```

### Encryption Setup

```bash
export DEVSYNTH_ENCRYPTION_AT_REST=true
export DEVSYNTH_ENCRYPTION_KEY="$(poetry run python -c 'from devsynth.security.encryption import generate_key; print(generate_key())')"
export DEVSYNTH_TLS_CERT_FILE=/path/to/cert.pem
export DEVSYNTH_TLS_KEY_FILE=/path/to/key.pem
```

## Security Audits

### Pre-Commit Security

```bash
# Run security audit
poetry run python scripts/security_audit.py

# Verify security policy compliance
poetry run python scripts/verify_security_policy.py

# Policy audit (check for hardcoded secrets)
poetry run python scripts/policy_audit.py
```

### Automated Security Scans

**Security Scanning Philosophy:**

**Thesis**: Automated security scanning provides continuous protection against vulnerabilities and ensures compliance with security policies.

**Antithesis**: Over-reliance on automated tools without human oversight can miss context-specific security issues and create false confidence.

**Synthesis**: Balanced security approach combining automated scanning with human review, dialectical analysis, and continuous monitoring ensures comprehensive protection.

### Security Scan Commands

```bash
# Static analysis with Bandit
poetry run bandit -r src/devsynth

# Dependency vulnerability scan with Safety
poetry run safety check

# Comprehensive security audit
DEVSYNTH_PRE_DEPLOY_APPROVED=true \
poetry run python scripts/security_audit.py --report security_audit.json

# Check for secrets in code
poetry run python scripts/policy_audit.py --secrets

# Verify security policy compliance
poetry run python scripts/verify_security_policy.py
```

### Security Environment Setup

**Required Security Flags:**
```bash
# Enable security features for testing
export DEVSYNTH_AUTHENTICATION_ENABLED=true
export DEVSYNTH_AUTHORIZATION_ENABLED=true
export DEVSYNTH_SANITIZATION_ENABLED=true
export DEVSYNTH_ENCRYPTION_AT_REST=true
export DEVSYNTH_ENCRYPTION_IN_TRANSIT=true
export DEVSYNTH_TLS_VERIFY=true

# Set secure access token (never commit)
export DEVSYNTH_ACCESS_TOKEN="<secure-token>"
```

**Security Tool Verification:**
```bash
# Verify security tools are available
poetry run which bandit
poetry run which safety
poetry run python -c "import devsynth.security.encryption; print('Security module OK')"
```

## Dialectical Audit Policy

Follow `docs/policies/dialectical_audit.md`:

### Mandatory Audit Resolution

**Before any commit or PR:**

```bash
poetry run python scripts/dialectical_audit.py
```

- CI fails if `dialectical_audit.log` contains unanswered questions
- Release verification halts if questions unresolved
- Log archived as workflow artifact

### Dialectical Notes in Changes

Include in PR descriptions for significant changes:

```markdown
## Dialectical Analysis

**Thesis**: Original approach was X because Y.

**Antithesis**: Problem identified - X doesn't handle Z case.

**Synthesis**: New approach combines X's benefits with Z handling.
```

Record test changes in `docs/rationales/test_fixes.md`.

## Secrets Management

- **Never commit secrets** to repository
- Store API keys in environment variables or secrets manager
- Use `.env` file locally (not committed)
- Verify `.env` permissions are restrictive (not symlink)

## Threat Model

Primary threats:
- Unauthorized access to memory stores
- Interception of API traffic
- Misuse of agent/API credentials

Mitigations:
- Encryption at rest and in transit
- TLS for network communication
- Bearer token authentication
- Routine dependency and static analysis

## Incident Response

```bash
# Collect logs and audit
python scripts/security_incident_response.py \
  --collect-logs \
  --audit \
  --output incident_$(date +%Y%m%d)
```

## Vulnerability Management

```bash
# Show outdated dependencies
python scripts/vulnerability_management.py

# Apply updates
python scripts/vulnerability_management.py --apply
```

## Periodic Review

Security policies reviewed quarterly. Check if review due:

```python
from datetime import date
from devsynth.security.review import is_review_due

if is_review_due(date(2024, 1, 1)):
    print("Security review required")
```

## Pre-Deployment Checklist

1. ✅ All security flags configured
2. ✅ `verify_security_policy.py` passes
3. ✅ `security_audit.py` passes
4. ✅ `dialectical_audit.log` resolved
5. ✅ No hardcoded secrets
6. ✅ Dependencies up to date
7. ✅ Audit report archived
