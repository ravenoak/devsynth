Feature: devsynth run-tests command
  As a developer
  I want to verify the test runner behavior
  So that the command handles different test selections

  Scenario: Successful test run exits with status 0
    Given the environment variable "PYTEST_ADDOPTS" is "-k test_run_tests_tool"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"
    Then the command should succeed

  Scenario: Empty test selection exits successfully
    Given the environment variable "PYTEST_ADDOPTS" is "-k nonexistent_test_keyword"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"
    Then the command should succeed
    And the output should mention no tests were run

  Scenario: Empty test selection runs in parallel without xdist assertions
    Given the environment variable "PYTEST_ADDOPTS" is "-k nonexistent_test_keyword"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast"
    Then the command should succeed
    And the output should mention no tests were run
    And the output should not contain xdist assertions

  Scenario: Failing tests return a non-zero exit code
    Given the environment variable "PYTEST_ADDOPTS" is "-k test_provider_logging"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"
    Then the command should fail

  Scenario: Maxfail option exits after first failure
    Given the environment variable "PYTEST_ADDOPTS" is "-k test_provider_logging"
    When I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1"
    Then the command should fail
