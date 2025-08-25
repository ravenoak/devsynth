# Requirements Traceability (TODO)

Status: TODO
Last reviewed: 2025-08-24
Owner: DevSynth Maintainers

Purpose:
- Provide bidirectional traceability between requirements (ReqIDs) and tests.
- Aggregate ReqID references from test docstrings as described in tests/README.md.

Planned approach:
- Implement a small extractor that scans tests/** for pytest tests, reading function/class docstrings and collecting patterns like `ReqID:` or `[ReqID:<ID>]`.
- Generate a markdown table mapping ReqIDs -> test paths and optionally test names.
- Optionally reverse map (tests -> ReqIDs) for completeness.
- Integrate as a script `scripts/generate_traceability.py` or extend existing tooling if present.

Interim policy (until automation is in place):
- Contributors should include a ReqID reference in new/modified tests' docstrings.
- PR reviewers verify presence of ReqID references.
- This document will be updated automatically once the extractor is implemented.

Open tasks:
- [ ] Implement extractor script per Planned approach.
- [x] Add CI wiring (.github/workflows/traceability.yml) to run the extractor and publish the report artifact.
- [ ] Backfill ReqID references across existing tests where missing.

Notes:
- See tests/README.md for guidance on ReqID tagging conventions.
- Keep output path consistent: docs/requirements_traceability.md.
