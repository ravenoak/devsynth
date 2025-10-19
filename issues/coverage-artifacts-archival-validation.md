# Coverage Artifacts Archival Validation and Docs Update

Date: 2025-10-18 22:57 local

Summary
- Validate that coverage artifacts (JSON/HTML) are produced, knowledge-graph banner is emitted, and archival to artifacts/releases/<release_tag>/<profile>/<timestamp>-<profile>/ occurs after a successful run.
- Refresh test_reports/coverage_manifest_latest.json and update documentation with run IDs and SHA-256 checksums.

Background
Recent changes ensure:
- _archive_coverage_artifacts invoked post-publication to copy:
  - coverage.json
  - htmlcov-<timestamp>-<profile>/
  - devsynth_run_tests_<profile>.log containing the “[knowledge-graph] …” banner
- coverage manifests are written to test_reports/coverage_manifest_<UTC>.json and test_reports/coverage_manifest_latest.json.

Acceptance Criteria
- A successful fast+medium run with --report completes locally without timeouts.
- coverage_manifest_latest.json exists and includes totals.percent_covered.
- Artifacts are archived under artifacts/releases/<release_tag>/<profile>/<timestamp>-<profile>/ with the three expected items present.
- docs/plan.md, docs/release/0.1.0-alpha.1.md, and docs/tasks.md §§30–31 updated with:
  - Run IDs (TestRun, QualityGate, Evidence IDs) from knowledge-graph banner/output
  - SHA-256 checksums of coverage.json and html index
- pre-commit hooks pass on updated files.

Reproduction Steps
1) Run smoke lane (quick diagnostics):
   poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

2) Full fast+medium with report (generates artifacts + knowledge graph):
   poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel

3) Validate outputs:
   - ls test_reports/coverage_manifest_latest.json
   - open test_reports/coverage_manifest_latest.json and confirm totals.percent_covered
   - Check artifacts/releases/<tag>/<profile>/<timestamp>-<profile>/ for coverage.json, htmlcov-<...>/, devsynth_run_tests_<profile>.log

4) Capture IDs and checksums:
   - Parse “[knowledge-graph] …” line from CLI output/log
   - Compute SHA-256 for coverage.json and html index if needed using scripts or devsynth.release.compute_file_checksum

5) Update docs and run hooks:
   - Edit docs/plan.md, docs/release/0.1.0-alpha.1.md, docs/tasks.md §§30–31
   - poetry run pre-commit run --files test_reports/coverage_manifest_latest.json docs/plan.md docs/release/0.1.0-alpha.1.md

Notes / Risks
- If the run times out in this environment, use segmented execution:
  poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel --segment --segment-size 50
- In smoke mode, coverage enforcement is set to non-fatal but artifacts should still be produced if pytest-cov is available.

Follow-ups
- If coverage is below threshold, update issues/coverage-below-threshold.md with new metadata and remediation tasks.
- If artifacts are missing, verify PYTEST_DISABLE_PLUGIN_AUTOLOAD and ensure '-p pytest_cov' is appended per CLI guidance.
