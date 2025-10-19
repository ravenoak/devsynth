Feature: Inspect Commands
  As a developer using DevSynth
  I want to use the inspect commands
  So that I can gain insights about my codebase and project configuration

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @code-analysis
  Scenario: Inspect code in the current directory
    When I run the command "devsynth inspect-code"
    Then the system should analyze the codebase in the current directory
    And the output should include architecture information
    And the output should include code quality metrics
    And the output should include test coverage information
    And the output should include project health score
    And the workflow should execute successfully

  @code-analysis
  Scenario: Inspect code in a specific directory
    When I run the command "devsynth inspect-code --path ./src"
    Then the system should analyze the codebase at "./src"
    And the output should include architecture information
    And the output should include code quality metrics
    And the output should include test coverage information
    And the output should include project health score
    And the workflow should execute successfully

  @code-analysis
  Scenario: Handle errors during code inspection
    Given a project with invalid code structure
    When I run the command "devsynth inspect-code"
    Then the system should display an error message
    And the error message should indicate the analysis problem

  @manifest-analysis
  Scenario: Analyze config in the current directory
    When I run the command "devsynth inspect-config"
    Then the system should analyze the project configuration
    And the output should include project information
    And the output should include structure information
    And the output should include directories information
    And the workflow should execute successfully

  @manifest-analysis
  Scenario: Analyze config in a specific directory
    When I run the command "devsynth inspect-config --path ./my-project"
    Then the system should analyze the project configuration at "./my-project"
    And the output should include project information
    And the output should include structure information
    And the output should include directories information
    And the workflow should execute successfully

  @manifest-analysis
  Scenario: Update config with new findings
    Given a project with outdated configuration
    When I run the command "devsynth inspect-config --update"
    Then the system should analyze the project configuration
    And the system should update the configuration with new findings
    And the output should indicate that the configuration was updated
    And the workflow should execute successfully

  @manifest-analysis
  Scenario: Prune config entries that no longer exist
    Given a project with configuration entries that no longer exist
    When I run the command "devsynth inspect-config --prune"
    Then the system should analyze the project configuration
    And the system should remove entries that no longer exist
    And the output should indicate that the configuration was pruned
    And the workflow should execute successfully

  @manifest-analysis
  Scenario: Handle missing configuration file
    Given a project without a configuration file
    When I run the command "devsynth inspect-config"
    Then the system should display a warning message
    And the warning message should indicate that no configuration file was found
