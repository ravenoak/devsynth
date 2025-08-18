# Issue 151: Normalize and verify test markers
Milestone: 0.1.0-alpha.1 (completed 2025-08-20)

The test suite must ensure each test file contains exactly one speed marker (`fast`, `medium`, or `slow`). Some tests lacked markers or requirement IDs, preventing consistent categorization.

## Progress
- 2025-08-20: Added missing speed markers and requirement IDs for prompt auto-tuning and EDRR coordinator tests; verification scripts report no outstanding marker issues.
- Status: closed
