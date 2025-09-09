# Issue: Missing ReqID Docstring Tags Across Tests

Date: 2025-09-02 10:24 local

Summary
- The new verification script scripts/verify_docstring_reqids.py reports that many test functions are missing the required "ReqID:" tag in their docstrings.
- This blocks Task 13 full completion (requirements traceability) until addressed.

Reproduction Commands
- Generate report (JSON + stdout):
  poetry run python scripts/verify_docstring_reqids.py --report --report-file diagnostics/test_reqids_report.json
- Taskfile wrapper (also appends diagnostics/exec_log.txt):
  task verify:reqids

Observed Output
- As of first run: 854 test(s) missing 'ReqID:' docstring tag.
- See diagnostics/verify_reqids_stdout.txt and diagnostics/test_reqids_report.json for details.

Artifacts
- diagnostics/test_reqids_report.json
- diagnostics/verify_reqids_stdout.txt
- diagnostics/exec_log.txt (entry appended by task verify:reqids)

Suspected Root Cause
- Historical tests lack ReqID annotations; no enforcement existed previously.

Proposed Resolution Plan
- Iterate through tests/ by priority (unit > integration > behavior), adding succinct ReqID tags to function docstrings.
- Enforce via pre-commit optional hook or CI advisory step using the new script.
- Track progress by decreasing missing_reqid_count in diagnostics/test_reqids_report.json over iterations.

Exit Criteria
- verify_docstring_reqids.py returns exit code 0 in project root.
- docs/tasks.md Task 13 remains partially complete until count reaches 0; then mark fully complete.
