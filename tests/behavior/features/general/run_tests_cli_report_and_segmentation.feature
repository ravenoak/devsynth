Feature: Run-tests CLI reporting, segmentation, and smoke behavior
  As a developer
  I want CLI flags to behave as documented
  So that reports are generated, segments are respected, and smoke mode isolates plugins

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: HTML report is generated when --report is passed
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --report"
    Then the command should exit successfully
    And a test HTML report should exist under "test_reports"

  Scenario: Segmentation flags are accepted and forwarded
    When I run the command "devsynth run-tests --target unit-tests --speed=fast --segment 2 --segment-size 5"
    Then the command should exit successfully
    And the segmentation should be reflected in the invocation

  Scenario: Smoke mode disables plugin autoload and isolation is applied
    When I run the command "devsynth run-tests --smoke --speed=fast"
    Then the command should exit successfully
    And plugin autoload should be disabled in the environment

  Scenario: Invalid speed value yields a helpful error
    When I run the command "devsynth run-tests --target unit-tests --speed warp"
    Then the command should fail with a helpful message containing "Invalid --speed value(s)"
