Milestone: 0.1.0-alpha.3
Status: open
Owner: Integrations Guild

Priority: high
Dependencies: src/devsynth/integrations/, docs/architecture/autoresearch_integration.md

## Problem Statement
Autoresearch telemetry currently relies on local fixtures. The naming policy now
reserves the Autoresearch brand for the external MCP/A2A client bridge, but DevSynth
still lacks a production-ready handshake that exchanges signed telemetry via the
Autoresearch APIs.

## Action Plan
- [ ] Finalise MCP session management against the Autoresearch sandbox.
- [ ] Implement the A2A channel orchestrator and map persona routing metadata.
- [ ] Execute SPARQL queries through the Autoresearch gateway to populate research telemetry overlays.
- [ ] Harden CLI and dashboard fallbacks once live telemetry replaces fixture bundles.

## Acceptance Criteria
- [ ] MCP handshake negotiates a session identifier and passes signature metadata to the A2A layer.
- [ ] A2A orchestrator attaches persona context and forwards SPARQL queries to the Autoresearch endpoint.
- [ ] Research telemetry payloads are generated via the external client without relying on local JSON fixtures.
- [ ] Documentation updates reference the live integration flow and enumerate rollback procedures.

## Evidence
- Pending once external handshake succeeds.

## References
- src/devsynth/integrations/autoresearch_client.py
- docs/user_guides/mvuu_dashboard.md
- docs/architecture/autoresearch_integration.md
