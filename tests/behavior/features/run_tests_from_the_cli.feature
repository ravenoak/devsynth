Feature: Run tests from the CLI
  As a developer working in a constrained environment
  I want segmentation fallbacks to be observable
  So that coverage sweeps stay predictable when the CLI cannot batch tests

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Segmentation falls back to a single batch without explicit speeds
    When I run the command "devsynth run-tests --target unit-tests --segment --segment-size 3 --no-parallel"
    Then the command should exit successfully
    And the CLI should request segmentation without explicit speeds
