Feature: Inspect Code Command
  As a developer
  I want to inspect a codebase and get architecture, quality, and health metrics
  So that I can understand the current state of the project and identify areas for improvement

  Background:
    Given the DevSynth CLI is installed
    And I have a project with source code

  Scenario: Inspect a codebase with default settings
    When I run the command "devsynth inspect-code"
    Then the command should execute successfully
    And the system should display architecture metrics
    And the system should display code quality metrics
    And the system should display health metrics

  Scenario: Inspect a codebase with a specific path
    When I run the command "devsynth inspect-code --path ./src"
    Then the command should execute successfully
    And the system should display metrics for the specified path
    And the metrics should be specific to the code in that path

  Scenario: Inspect a codebase with verbose output
    When I run the command "devsynth inspect-code --verbose"
    Then the command should execute successfully
    And the system should display detailed metrics
    And the metrics should include explanations and recommendations

  Scenario: Inspect a codebase and generate a report
    When I run the command "devsynth inspect-code --report report.json"
    Then the command should execute successfully
    And the system should generate a report file
    And the report should contain all the metrics

  Scenario: Inspect a non-existent path
    When I run the command "devsynth inspect-code --path ./non_existent_dir"
    Then the command should fail
    And the system should display an error message indicating the path does not exist
