---
title: Enhanced Test Parser Parity Report Guide
date: 2025-08-26
status: published
version: 0.1.0a1
---

# Enhanced Test Parser Parity — How to Run and Interpret

This guide explains how to exercise scripts/enhanced_test_parser.py against the test suite and how to interpret parity results when compared to pytest collection. It aligns with project guidelines (run via Poetry; offline-first) and docs/plan.md (determinism and diagnostics).

## How to run

Preferred via Poetry for consistent plugins and env:

```bash
poetry install --with dev --extras tests
poetry run bash scripts/diagnostics/run_enhanced_parser_parity.sh
```

This generates a JSON artifact at:

- test_reports/enhanced_parser_parity.json

Alternatively, run directly with explicit directory and JSON output:

```bash
poetry run python scripts/enhanced_test_parser.py \
  --directory tests \
  --compare \
  --report \
  --report-file test_reports/enhanced_parser_parity.json
```

## What the report contains

- parser_count: Number of tests detected by the AST-based parser
- pytest_count: Number of tests reported by pytest --collect-only -q
- common_count: Overlap between both collectors
- only_in_parser/only_in_pytest (+_count): Discrepancies on each side
- discrepancy: Absolute difference in total counts

## Known limitations and interpretation notes

These are expected and documented to prevent false alarms:

- Dynamic test generation: pytest may collect tests created at import/runtime that the AST parser cannot see. Expect some entries under only_in_pytest.
- Path formatting: Minor differences in node IDs (e.g., parameterization IDs) may cause apparent deltas even when coverage is functionally equivalent.
- Skips/xfails via import-time conditions: pytest may skip-but-still-collect items; the AST parser reports them as plain tests.
- Non-standard patterns: Custom decorators or meta-programming may evade AST heuristics.

When evaluating parity, focus on:

- Large, systemic discrepancies (indicate real gaps)
- Repeated patterns in only_in_pytest pointing to specific constructs we can enhance
- Safety: The AST parser must never over-report behavior/BDD tests if excluded by policy (see pytest.ini bdd_features_base_dir)

## Next steps when discrepancies are significant

- Capture concrete examples from only_in_pytest and add reduced repros in tests/templates/ for parser enhancement work.
- Extend TestVisitor for the specific pattern, guarded by unit tests.
- Re-run the parity script and append a short dialectical note to docs/rationales/test_fixes.md when significant.

## References

- scripts/enhanced_test_parser.py
- docs/developer_guides/enhanced_test_parser.md (capabilities and CLI)
- project guidelines (testing discipline)
- docs/plan.md (stabilization priorities)
