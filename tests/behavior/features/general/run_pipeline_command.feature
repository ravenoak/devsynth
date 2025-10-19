Feature: Run Pipeline Command
  As a developer
  I want to execute generated code using the CLI
  So that I can run tests and verify the implementation

  Background:
    Given the DevSynth CLI is installed
    And I have a project with generated code

  Scenario: Run unit tests with default settings
    When I run the command "devsynth run-pipeline --target unit-tests"
    Then the command should execute successfully
    And the system should run the unit tests
    And the system should display test results

  Scenario: Run integration tests with default settings
    When I run the command "devsynth run-pipeline --target integration-tests"
    Then the command should execute successfully
    And the system should run the integration tests
    And the system should display test results

  Scenario: Run behavior tests with default settings
    When I run the command "devsynth run-pipeline --target behavior-tests"
    Then the command should execute successfully
    And the system should run the behavior tests
    And the system should display test results

  Scenario: Run all tests with verbose output
    When I run the command "devsynth run-pipeline --target all-tests --verbose"
    Then the command should execute successfully
    And the system should run all tests
    And the system should display detailed test results

  Scenario: Run a specific test file
    When I run the command "devsynth run-pipeline --target unit-tests --file tests/test_example.py"
    Then the command should execute successfully
    And the system should run the specified test file
    And the system should display test results for that file

  Scenario: Run tests with a non-existent target
    When I run the command "devsynth run-pipeline --target non-existent-target"
    Then the command should fail
    And the system should display an error message about the invalid target
