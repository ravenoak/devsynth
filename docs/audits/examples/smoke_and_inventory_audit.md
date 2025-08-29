# Command Audit Log — Smoke and Inventory (Example)

- Command: task tests:sanity-and-inventory
- Runner: local (example)
- Start time: 2025-08-28 16:25
- End time: 2025-08-28 16:27
- Exit code: 0 (example)
- Duration: ~120s (example)

Artifacts and key outputs (example paths):
- Collection-only output: test_reports/collect_only_output.txt
- Smoke plugin notice: test_reports/smoke_plugin_notice.txt (expected content starts with "PASS: plugin autoload disabled notice detected")
- Smoke timing: test_reports/smoke_fast_timing.txt (< 60s target on CI)
- Inventory JSON: test_reports/test_inventory.json (exists, valid JSON)

Notes:
- This file is a filled example based on the template at docs/audits/command_audit_template.md. Replace placeholders with real timestamps and durations after running the Taskfile target.
- Use this as a reference for Section 7 acceptance evidence in CI and local runs.
