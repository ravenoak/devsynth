# Evaluate migration to NiceGUI post-0.1.0a1

Status: Proposed (post-0.1.0a1 follow-up)
Owner: Interface WG

Context
- For 0.1.0a1, the canonical WebUI extra is streamlit (see docs/developer_guides/testing.md and pyproject extras alignment).
- NiceGUI offers a richer desktop-like UI and may be preferable long-term.

Scope
- Assess feasibility, developer ergonomics, headless execution, and testability under CI constraints.
- Inventory current streamlit-dependent modules and behavior tests.
- Propose an abstraction layer (if needed) to decouple UI framework specifics.

Acceptance Criteria
- Decision document comparing Streamlit vs NiceGUI trade-offs.
- Spike or prototype demonstrating parity for one representative UI path.
- Plan for migration (if chosen) without disrupting minimal contributor workflows.

References
- docs/plan.md §J WebUI Framework Alignment Plan
- docs/developer_guides/testing.md (webui extra guidance)
