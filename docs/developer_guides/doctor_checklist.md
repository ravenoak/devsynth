# DevSynth Doctor Triage Checklist

Status: initial version (2025-09-04)

Purpose
- Provide a quick triage flow for common diagnostics surfaced by `poetry run devsynth doctor`.
- Complement diagnostics/doctor.txt with actionable fixes and references to configuration docs.

How to run
- poetry shell (optional) or prefix commands with `poetry run`
- Run: `poetry run devsynth doctor`
- Open latest diagnostics file: `diagnostics/doctor.txt`

Common findings and actions
- Missing provider API keys (e.g., OPENAI/ANTHROPIC)
  - Default behavior for tests is offline stub mode. For opt-in real backends, export required env vars:
    - `export OPENAI_API_KEY=...`
    - `export ANTHROPIC_API_KEY=...`
  - Also set provider selection if needed:
    - `export DEVSYNTH_PROVIDER=openai` (default is overridden to `stub` by run-tests in test mode)
- Environment schema keys missing (application, agents, edrr)
  - Run `poetry run devsynth init` to generate defaults, then edit config files under `config/` as needed.
- Feature flags missing (e.g., prompt_auto_tuning)
  - Add to your environment config or export feature flags, e.g.:
    - `export DEVSYNTH_FEATURE_PROMPT_AUTO_TUNING=false`
- Staging/production env var references unset
  - Only required when running those environments. For local tests, keep offline defaults. For staging/production, set variables; see README and docs for deployment.
- ChromaDB host/port types
  - Ensure `DEVSYNTH_CHROMADB_PORT` is an integer. Example:
    - `export DEVSYNTH_CHROMADB_PORT=8000`

Integration with testing workflow
- Smoke mode intentionally disables third-party plugins and enforces no-parallel. Use:
  - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
- Resource-gated tests are skipped unless you opt in via env flags, e.g.:
  - `export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true`
  - `export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true`

References
- Plan: docs/plan.md (D3 and acceptance AC6)
- Testing guide: docs/developer_guides/testing.md
- Diagnostics snapshot: diagnostics/doctor.txt
