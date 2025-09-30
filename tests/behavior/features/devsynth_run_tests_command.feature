Feature: devsynth run-tests command
  Verify the run-tests command handles missing optional dependencies.

  Scenario: run-tests defaults to skipping optional LM Studio tests
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is unset
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"
    Then the command should succeed

  Scenario: run-tests in parallel skips optional providers
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is "false"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast"
    Then the command should succeed
    And the output should not contain xdist assertions

  Scenario: run-tests can segment execution
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is "false"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --segment --segment-size=1"
    Then the command should succeed

  Scenario: run-tests accepts feature flags
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is "false"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --feature experimental"
    Then the command should succeed

  Scenario: run-tests produces coverage for fast and medium speeds
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is "false"
    When I invoke "devsynth run-tests --speed=fast --speed=medium --report --no-parallel"
    Then the command should succeed
    And the coverage report "test_reports/coverage.json" should exist
    And the coverage report speeds should include "fast" and "medium"
