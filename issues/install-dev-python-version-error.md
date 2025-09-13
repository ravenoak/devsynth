Title: install_dev.sh reports missing Python 3.12 for Poetry
Date: 2025-09-13 00:00 UTC
Status: open
Affected Area: environment
Reproduction:
  - Run `bash scripts/install_dev.sh` on a fresh environment.
  - Script logs `[error] Python 3.12 not available for Poetry` and exits.
Exit Code: non-zero
Artifacts:
  - /tmp/install_dev.log
Suspected Cause: Poetry's Python discovery fails when using pyenv shims.
Next Actions:
  - [ ] Detect available Python 3.12 via `pyenv which python3.12` before calling `poetry env use`.
  - [ ] Ensure script falls back gracefully if Poetry cannot switch interpreters.
Progress:
  - 2025-09-13: Issue created after setup failure during smoke test run.
Resolution Evidence:
  - docs/tasks.md item 15.4
