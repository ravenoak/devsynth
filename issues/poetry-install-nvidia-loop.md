---
Title: poetry install hangs on nvidia package
Date: 2025-09-08 10:00 local
Status: closed
Affected Area: infra
Reproduction:
  - poetry install --with dev --all-extras
Exit Code: 0
Artifacts:
  - diagnostics/poetry_install_hang.txt
Suspected Cause: installation repeatedly reinstalls nvidia/__init__.py and never completes.
Next Actions:
  - [x] Pin or remove problematic nvidia dependency.
  - [x] Retry poetry install after adjustment.
Resolution Evidence:
  - diagnostics/poetry_install_hang.txt shows successful install
---
