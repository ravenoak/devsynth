---
Title: Provider authentication optional dependencies
Date: 2025-10-22 06:03 UTC
Status: closed
Affected Area: security
Reproduction:
  - `poetry run pytest tests/unit/security/test_authentication_optional_dependency.py -q`
  - `poetry run task mypy:strict`
Exit Code: 0
Artifacts:
  - console logs from the commands above
Suspected Cause: Argon2 was a hard dependency that raised at import time without guidance, blocking environments without the security extra.
Next Actions:
  - [x] Guard Argon2 imports with a stub that raises a guided ImportError only when authentication stays enabled.
  - [x] Add fast regression coverage that exercises the fallback when Argon2 is missing.
  - [x] Document mandatory extras in docs/setup/environment.md and scripts/install_dev.sh messaging.
Resolution Evidence:
  - See pytest and mypy outputs captured in this change set.
---
