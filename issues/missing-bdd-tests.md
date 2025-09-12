# Missing BDD tests
Milestone: 0.1.0a1
Status: open
Priority: medium
Dependencies:

## Problem Statement
Many specifications lack corresponding behavior-driven tests, which limits confidence that 90% coverage reflects system-wide behavior.

## Action Plan
- Inventory specifications without BDD feature files or step definitions.
- Implement missing features under tests/behavior/features/ and link them to their specifications.
- Update coverage reports once scenarios are in place.

## Acceptance Criteria
- Each identified specification has a matching BDD feature file.
- Aggregated coverage with new behavior tests continues to meet the 90% threshold.
