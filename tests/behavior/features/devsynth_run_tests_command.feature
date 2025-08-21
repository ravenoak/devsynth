Feature: devsynth run-tests command
  Verify the run-tests command handles missing optional dependencies.

  Scenario: run-tests succeeds without optional LLM providers
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is "false"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"
    Then the command should succeed

  Scenario: run-tests in parallel skips optional providers
    Given the environment variable "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE" is "false"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast"
    Then the command should succeed
    And the output should not contain xdist assertions
