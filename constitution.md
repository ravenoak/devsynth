# DevSynth Project Constitution

## Technology Stack

**Framework**: DevSynth 0.1.0a1 (Agentic Software Engineering Platform)
**Language**: Python 3.12 with comprehensive type annotations
**Architecture**: Hexagonal architecture with hexagonal ports and adapters
**Testing**: Behavior-Driven Development (BDD) with Gherkin scenarios
**Methodology**: EDRR (Expand-Differentiate-Refine-Retrospect) methodology
**Documentation**: Specification-driven with living documentation system

## Architectural Patterns

**Agent System**: Multi-agent collaboration via WSDE model with dialectical reasoning
**Memory System**: Hybrid memory with Kuzu (graph), ChromaDB (vector), and RDFLib (knowledge graph) backends
**Development Process**: Specification-first with intent as source of truth
**Quality Gates**: Dialectical audit policy and comprehensive test coverage (>90%)
**Configuration**: Unified YAML/TOML loader with environment variable support

## Coding Standards

**Documentation**: All public APIs require comprehensive docstrings with examples
**Testing**: Every feature must have BDD scenarios and unit tests with speed markers
**Commit Messages**: Follow Conventional Commits specification (feat:, fix:, docs:, etc.)
**Code Style**: Black formatting with strict mypy type checking and pre-commit hooks
**Import Organization**: Group imports by type (stdlib, third-party, local) with blank lines

## Development Workflow

### EDRR Methodology Integration
1. **Expand**: Generate multiple diverse approaches, explore alternatives, gather context
2. **Differentiate**: Compare options, evaluate against requirements, identify trade-offs
3. **Refine**: Implement chosen solution, optimize for quality, add comprehensive tests
4. **Retrospect**: Analyze outcomes, capture learnings, suggest improvements

### Specification-Driven Development (SDD)
1. **Specify**: Define "what" and "why" in natural language with user stories
2. **Plan**: Transform "what" into "how" with technical implementation planning
3. **Tasks**: Break specification into actionable, reviewable work units
4. **Implement**: Execute tasks to generate production-ready code with tests

### Behavior-Driven Development (BDD)
- Use Gherkin syntax in `.feature` files for executable specifications
- Follow Given-When-Then structure with declarative style
- Each scenario must be atomic and test a single business rule
- Background steps for common preconditions across scenarios

## Non-Functional Requirements

**Performance**: Sub-200ms response times for API endpoints, sub-500ms for CLI commands
**Reliability**: 99.9% uptime with graceful degradation and comprehensive error handling
**Security**: Input validation, sanitization, and audit trails with security policy compliance
**Scalability**: Horizontal scaling support with stateless services and connection pooling
**Maintainability**: Modular architecture with clear separation of concerns and comprehensive documentation

## Quality Standards

**Test Coverage**: Minimum 90% coverage with coverage gates enforced in CI
**Speed Markers**: All tests must have speed markers (fast, medium, slow) for parallel execution
**Resource Gates**: Optional services guarded with environment variables (DEVSYNTH_RESOURCE_*)
**Dialectical Audit**: All changes must pass dialectical audit policy before submission

## Agent Collaboration Guidelines

**WSDE Model**: Use Primus (coordinator), Worker (executor), Supervisor (monitor), Designer (creative), and Evaluator (analysis) roles
**Consensus Building**: Require consensus for critical architectural decisions with configurable thresholds
**Memory Integration**: Leverage hybrid memory system for context and learning across sessions
**Tool Usage**: Appropriate tool selection based on task complexity and requirements

## Cursor IDE Integration

**Rules**: Always apply architecture and EDRR framework rules for context
**Commands**: Use structured commands for common workflows (expand, differentiate, refine, retrospect)
**Modes**: Configure custom modes for specialized tasks (EDRRImplementer, SpecArchitect)
**Specifications**: Reference docs/specifications/ for all development decisions
**BDD Integration**: Ensure Gherkin scenarios in tests/behavior/features/ drive implementation

## Documentation Standards

**Living Documentation**: Specifications evolve with implementation, maintain traceability
**Format**: Markdown with consistent structure, metadata, and cross-references
**Validation**: Automated validation of documentation completeness and consistency
**Accessibility**: Clear breadcrumbs, comprehensive index, and searchable content

## Release and Deployment

**Versioning**: Semantic versioning with pre-release tags for experimental features
**CI/CD**: Comprehensive testing pipeline with smoke, unit, integration, and behavior tests
**Deployment**: Infrastructure-as-code with health checks and rollback capabilities
**Monitoring**: Observability with metrics, logging, and alerting for production systems

## Continuous Improvement

**Dialectical Audit**: Regular review of processes and outcomes for improvement opportunities
**Requirements Traceability**: Maintain links between requirements, specifications, code, and tests
**Performance Monitoring**: Continuous measurement and optimization of system performance
**Learning Integration**: Capture and apply learnings from retrospectives across projects

---
*Last updated: October 22, 2025*
*This constitution serves as the source of truth for all development activities in the DevSynth project.*
