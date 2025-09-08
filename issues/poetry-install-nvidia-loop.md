---
Title: poetry install hangs on nvidia package
Date: 2025-09-08 10:00 local
Status: open
Affected Area: infra
Reproduction:
  - poetry install --with dev --all-extras
Exit Code: 130
Artifacts:
  - diagnostics/poetry_install_hang.txt
Suspected Cause: installation repeatedly reinstalls nvidia/__init__.py and never completes.
Next Actions:
  - [ ] Pin or remove problematic nvidia dependency.
  - [ ] Retry poetry install after adjustment.
Resolution Evidence:
  - pending
---
