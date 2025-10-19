Feature: Test Metrics
  As a developer using DevSynth
  I want to analyze test-first development metrics
  So that I can ensure my development process follows best practices

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project
    And the project has a Git repository

  @test-metrics
  Scenario: Analyze test metrics with default parameters
    When I run the command "devsynth test-metrics"
    Then the system should analyze the last 30 days of commit history
    And the output should include test-first development metrics
    And the output should include test coverage metrics
    And the workflow should execute successfully

  @test-metrics
  Scenario: Analyze test metrics with custom time period
    When I run the command "devsynth test-metrics --days 60"
    Then the system should analyze the last 60 days of commit history
    And the output should include test-first development metrics
    And the output should include test coverage metrics
    And the workflow should execute successfully

  @test-metrics
  Scenario: Output test metrics to file
    When I run the command "devsynth test-metrics --output ./metrics-report.md"
    Then the system should analyze the last 30 days of commit history
    And the system should save the metrics to "./metrics-report.md"
    And the output should indicate that the report was saved
    And the workflow should execute successfully

  @test-metrics
  Scenario: Handle repository with no commits
    Given a project with no commit history
    When I run the command "devsynth test-metrics"
    Then the system should display a warning message
    And the warning message should indicate that no commits were found
    And the workflow should execute successfully

  @test-metrics
  Scenario: Handle repository with no tests
    Given a project with no test files
    When I run the command "devsynth test-metrics"
    Then the system should display a warning message
    And the warning message should indicate that no test files were found
    And the output should include recommendations for test-first development
    And the workflow should execute successfully
