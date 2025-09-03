# Issues Review Protocol (DevSynth 0.1.0a1)

This directory holds lightweight issue records used during pre‑release stabilization. Follow this protocol:

- When a non‑green run occurs (tests or guardrails), create or update an issue markdown file under issues/ with:
  - Title and date
  - Reproduction command(s)
  - Exit code
  - Diagnostics artifact paths (under diagnostics/ or test_reports/)
  - Suspected root cause and next actions
  - Status: open/closed; Close only after a green re‑run with artifacts attached.
- Reference the issue ID/file name in related commits and PR titles.

Template:

---
Title: `concise title`
Date: `YYYY‑MM‑DD HH:MM local`
Status: open | closed
Affected Area: `tests|guardrails|provider|docs|infra`
Reproduction:
  - `command`
Exit Code: `int`
Artifacts:
  - diagnostics/`file`
  - test_reports/`file`
Suspected Cause: `text`
Next Actions:
  - [ ] step 1
  - [ ] step 2
Resolution Evidence:
  - link to green run artifacts
---

Example issue files may be added and updated during iterations.
