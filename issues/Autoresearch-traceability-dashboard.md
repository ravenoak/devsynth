Milestone: 0.1.0-alpha.2
Status: open
Owner: Observability Guild

Priority: medium
Dependencies: docs/analysis/mvuu_dashboard.md, docs/analysis/autoresearch_evaluation.md

## Problem Statement
Traceability dashboards highlight MVUU entries but lack contextual overlays that
link Autoresearch activities to knowledge graph hops, agent roles, and resulting
commits. Without these views, stakeholders cannot audit how research questions
translate into implementation work.

## Action Plan
- [ ] Add optional Autoresearch overlays (timeline, provenance filters, integrity
      checks) to the MVUU dashboard UI.
- [ ] Teach CLI commands to emit structured Autoresearch telemetry compatible
      with MVUU visualisations.
- [ ] Provide export routines that redact sensitive fields by default while
      preserving verification hashes.
- [ ] Document dashboard toggles and workflow guidance for Autoresearch reviews.

## Acceptance Criteria
- [ ] MVUU dashboard renders Autoresearch overlays without breaking baseline
      TraceID views when overlays are disabled.
- [ ] CLI telemetry includes knowledge graph references, agent persona metadata,
      and digital signatures for research artefacts.
- [ ] Automated tests exercise overlay toggles and integrity checks.
- [ ] User guides describe Autoresearch review flows and privacy safeguards.

## References
- docs/analysis/mvuu_dashboard.md
- docs/analysis/autoresearch_evaluation.md
- docs/specifications/wsde-agent-model-refinement.md
