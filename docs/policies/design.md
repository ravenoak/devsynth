# Design Policy

This policy defines best practices for system architecture, design documentation, and review in DevSynth.

## Key Practices
- Maintain a clear architecture/design document in `docs/architecture/` (overview, diagrams, component responsibilities).
- Document architectural principles, design patterns, and interface/API contracts.
- Include data models, schemas, and security/privacy design in the design docs.
- Use design review and approval before implementation (store proposals in `docs/adr/` or as design RFCs).
- Reference requirement IDs in design artifacts for traceability.

## Artifacts
- Architecture Overview: `docs/architecture/overview.md`
- Component/Pattern Guides: `docs/architecture/hexagonal_architecture.md`, etc.
- API/Data Schemas: `docs/technical_reference/api_reference/`, `docs/architecture/`
- Security/Privacy Design: `docs/architecture/security_design.md` (if present)
- Design Decisions: `docs/adr/` (if present)

## References
- See [Requirements Policy](requirements.md) for traceability.
- See [Development Policy](development.md) for implementation standards.

