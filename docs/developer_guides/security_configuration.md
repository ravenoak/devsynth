---

author: DevSynth Team
date: '2025-07-15'
last_reviewed: '2025-07-15'
status: published
tags:
- developer-guide
- security
- deployment
- issue-104

title: Security Configuration Guidelines
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Security Configuration Guidelines
</div>

# Security Configuration Guidelines

This guide describes recommended security settings for deploying DevSynth in production.
It complements the secure coding guidance and addresses outstanding recommendations
from the [critical recommendations report](../analysis/critical_recommendations.md).
See [issue 104](../../issues/Critical-recommendations-follow-up.md) for background.

## Container Security

- **Non-root execution**: Containers should run as a dedicated user. The provided
  Kubernetes deployment manifests use `runAsUser: 1000` and disable privilege escalation.
- **Read-only filesystems**: Enable `readOnlyRootFilesystem` where possible to
  reduce the impact of a compromise.
- **Health checks**: Configure liveness and readiness probes to detect failures early.

## TLS Configuration

If using HTTPS or mutual TLS, set the following environment variables:

```bash
TLS_VERIFY=true
TLS_CERT_FILE=/path/to/cert.pem
TLS_KEY_FILE=/path/to/key.pem
TLS_CA_FILE=/path/to/ca.pem
```

These values map to the `security.tls` section of `config/default.yml` and can be
provided via Kubernetes secrets or Docker secrets.

## Secrets Management

- Store API keys and sensitive configuration in environment variables or secrets
  providers. Do not commit them to the repository.
- Rotate credentials regularly and audit access to secret storage.

## Dependency Security

- Run `poetry export --without-hashes --format=requirements.txt > requirements.txt` and
  scan the resulting file with tools such as `pip-audit`.
- Keep dependencies up to date and monitor CVE databases for vulnerabilities.

## Logging and Monitoring

- Ensure structured logging is enabled with correlation IDs.
- Forward logs to a secure location for retention and analysis.
- Monitor metrics and configure alerts for abnormal behavior.

---

Following these guidelines helps meet the security objectives outlined in the
critical recommendations report and improves DevSynth's deployment posture.
