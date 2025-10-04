Feature: Run-tests CLI reporting, segmentation, and smoke behavior
  As a developer
  I want CLI flags to behave as documented
  So that reports are generated, segments are respected, and smoke mode isolates plugins

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

# SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "--report emits HTML and JSON coverage artifacts summarizing executed speed profiles for audit trails."
  Scenario: HTML report is generated when --report is passed
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --report"
    Then the command should exit successfully
    And a test HTML report should exist under "test_reports"

# SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "--segment runs tests in batches; --segment-size sets batch size (default 50)."
  Scenario: Segmentation flags are accepted and forwarded
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --segment --segment-size 5"
    Then the command should exit successfully
    And the segmentation should be reflected in the invocation

# SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "Optional providers are disabled by default unless their DEVSYNTH_RESOURCE_* variables are explicitly set."
  Scenario: Optional providers default to disabled when not opted in
    Given optional providers are not preconfigured
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --no-parallel"
    Then the command should exit successfully
    And the run-tests invocation should disable the "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" provider

# SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "Successful runs enforce a minimum coverage threshold of DEFAULT_COVERAGE_THRESHOLD (90%) whenever coverage instrumentation is active; the CLI prints a success banner when the gate is met and exits with an error if coverage falls below the limit."
  Scenario: Coverage banner celebrates meeting the enforcement threshold
    Given coverage enforcement is configured to report 92.0 percent
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --no-parallel --report"
    Then the command should exit successfully
    And the coverage banner should confirm the coverage threshold gate was met

# SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "Successful runs enforce a minimum coverage threshold of DEFAULT_COVERAGE_THRESHOLD (90%) whenever coverage instrumentation is active; the CLI prints a success banner when the gate is met and exits with an error if coverage falls below the limit."
  Scenario: Coverage enforcement fails when the reported percentage drops below the gate
    Given coverage enforcement will fail with 85.0 percent
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --no-parallel --report"
    Then the command should fail with a helpful message containing "Coverage 85.00% is below the 90% gate"

  Scenario: Smoke mode disables plugin autoload and isolation is applied
    When I run the command "devsynth run-tests --smoke --speed=fast"
    Then the command should exit successfully
    And plugin autoload should be disabled in the environment

  Scenario: Invalid speed value yields a helpful error
    When I run the command "devsynth run-tests --target unit-tests --speed warp"
    Then the command should fail with a helpful message containing "Invalid --speed value(s)"
