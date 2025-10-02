Milestone: 0.1.0-alpha.2
Status: closed
Owner: Observability Guild

Priority: medium
Dependencies: docs/analysis/mvuu_dashboard.md, docs/analysis/autoresearch_evaluation.md

## Problem Statement
Traceability dashboards highlight MVUU entries but lack contextual overlays that
link Autoresearch activities to knowledge graph hops, agent roles, and resulting
commits. Without these views, stakeholders cannot audit how research questions
translate into implementation work.

## Action Plan
- [x] Add optional Autoresearch overlays (timeline, provenance filters, integrity
      checks) to the MVUU dashboard UI.
- [x] Teach CLI commands to emit structured Autoresearch telemetry compatible
      with MVUU visualisations.
- [x] Provide export routines that redact sensitive fields by default while
      preserving verification hashes via signed telemetry bundles.
- [x] Document dashboard toggles and workflow guidance for Autoresearch reviews.

## Acceptance Criteria
- [x] MVUU dashboard renders Autoresearch overlays without breaking baseline
      TraceID views when overlays are disabled.
- [x] CLI telemetry includes knowledge graph references, agent persona metadata,
      and digital signatures for research artefacts.
- [x] Automated tests exercise overlay toggles and integrity checks.
- [x] User guides describe Autoresearch review flows and privacy safeguards.

## Evidence
- Autoresearch overlay mock-up: `artifacts/mvuu_overlay_mock.html`
- Telemetry snapshot: `artifacts/mvuu_autoresearch_overlay_snapshot.json`
- User guidance: `docs/user_guides/mvuu_dashboard.md`

## Resolution (2025-10-01)
- Acceptance criteria met with overlays, telemetry exports, and documentation updates archived for 0.1.0a1. See the overlay mock (`artifacts/mvuu_overlay_mock.html`), signed telemetry snapshot (`artifacts/mvuu_autoresearch_overlay_snapshot.json`), and MVUU user guide (`docs/user_guides/mvuu_dashboard.md`) for the implementation evidence. Next milestone tracks external connector integration so live Autoresearch telemetry can replace the current stubs.
- Naming policy refreshed in 2025-10 to reserve the Autoresearch label for external client integrations. In-repo telemetry helpers now live under `src/devsynth/interface/research_telemetry.py`, with MCP/A2A hand-off scaffolding tracked in `src/devsynth/integrations/`.

## References
- docs/analysis/mvuu_dashboard.md
- docs/analysis/autoresearch_evaluation.md
- docs/specifications/wsde-agent-model-refinement.md
