# Secrets Management Policy

Last updated: 2025-08-25

This project must never store live secrets in the repository. All secrets must be
provided at runtime via environment variables or from an approved secret store.

Principles
- No secrets in VCS: source files, docs, examples, tests must not contain live secrets.
- Use placeholders: if demonstrating configuration, use placeholders like `<YOUR-API-KEY>`
  or `test-openai-key`.
- Prefer environment variables in local workflows (documented in README/guides) and
  GitHub Actions Secrets for CI.

Enforcement
- A lightweight secret scanner (scripts/check_no_secrets.py) runs in CI to catch common
  secret patterns (OpenAI keys, AWS keys, private keys, GitHub PATs, Slack tokens).
- Security workflows also run Bandit and Safety.

How to provide secrets locally
- Export environment variables in your shell before running commands, e.g.:
  export OPENAI_API_KEY=<YOUR-API-KEY>
- Avoid committing .env files. If you use .env locally, ensure it is ignored and never
  committed.

Rotation and revocation
- If a secret is accidentally exposed, immediately rotate it in the provider dashboard
  and revoke the old one. Then purge the secret from the history or invalidate the file.

Reporting and false positives
- If the scanner flags a false positive, prefer adjusting the content to use placeholders.
  As a last resort, update ALLOWLIST_SUBSTRINGS in scripts/check_no_secrets.py with caution.
