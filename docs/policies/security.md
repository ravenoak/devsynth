# Security Policy

This policy outlines security design principles and operational guidelines for DevSynth.

## Design Guidelines
- Apply the principle of least privilege for all agents and services.
- Encrypt sensitive data in transit and at rest where possible.
- Validate all environment variables and configuration inputs on startup.
- Keep dependencies patched and monitor vulnerability advisories.
- Document threat models and mitigations in the architecture docs.

## Operational Guidelines
- Enable or disable authentication, authorization and input sanitization via environment variables (`DEVSYNTH_AUTHENTICATION_ENABLED`, `DEVSYNTH_AUTHORIZATION_ENABLED`, `DEVSYNTH_SANITIZATION_ENABLED`).
- Encryption at rest for memory stores can be toggled with `DEVSYNTH_ENCRYPTION_AT_REST` and a base64 key provided via `DEVSYNTH_ENCRYPTION_KEY`.
- TLS verification and certificates are configured using `DEVSYNTH_TLS_VERIFY`, `DEVSYNTH_TLS_CERT_FILE`, `DEVSYNTH_TLS_KEY_FILE` and `DEVSYNTH_TLS_CA_FILE`.
- Store API keys and secrets in environment variables or a secrets manager; never commit them to the repository.
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
```
