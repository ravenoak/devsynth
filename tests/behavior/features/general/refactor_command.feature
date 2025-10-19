Feature: Refactor Command
  As a developer
  I want to get suggestions for next workflow steps using the CLI
  So that I can improve my codebase efficiently

  Background:
    Given the DevSynth CLI is installed
    And I have a project with source code

  Scenario: Get refactoring suggestions for a project
    When I run the command "devsynth refactor"
    Then the command should execute successfully
    And the system should display refactoring suggestions
    And the suggestions should include actionable steps

  Scenario: Get refactoring suggestions with a specific focus
    When I run the command "devsynth refactor --focus error-handling"
    Then the command should execute successfully
    And the system should display refactoring suggestions focused on error handling
    And the suggestions should include actionable steps

  Scenario: Get refactoring suggestions with verbose output
    When I run the command "devsynth refactor --verbose"
    Then the command should execute successfully
    And the system should display detailed refactoring suggestions
    And the suggestions should include reasoning and context

  Scenario: Get refactoring suggestions for a specific file
    When I run the command "devsynth refactor --file src/main.py"
    Then the command should execute successfully
    And the system should display refactoring suggestions for the specified file
    And the suggestions should be specific to the file's content

  Scenario: Get refactoring suggestions for a non-existent file
    When I run the command "devsynth refactor --file non_existent_file.py"
    Then the command should fail
    And the system should display an error message indicating the file does not exist
