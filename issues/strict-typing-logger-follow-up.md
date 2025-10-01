Title: Follow-up: restore strict typing for logger
Date: 2025-09-13 17:05 UTC
Status: open
Owner: Orion
Timeline: 2025-10-01
Affected Area: typing
Reproduction:
  - N/A (planning)
Exit Code: N/A
Artifacts:
  - N/A
Suspected Cause: Strict typing temporarily relaxed for logger.
Next Actions:
  - [ ] Reintroduce strict typing for logger.
  - [ ] Remove temporary mypy overrides.
Resolution Evidence:
  - 2025-10-01: `logging_setup` now enforces strict typing, including context-var aware metadata and JSON formatter checks; new unit coverage locks in request metadata serialization. Remaining hotspot: `devsynth.utils.logging` still mirrors legacy wrappers.
