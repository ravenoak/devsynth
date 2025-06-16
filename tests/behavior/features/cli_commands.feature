
Feature: CLI Command Execution
  As a developer
  I want to use the DevSynth CLI commands
  So that I can manage my development workflow efficiently

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Display help information
    When I run the command "devsynth help"
    Then the system should display the help information
    And the output should include all available commands
    And the output should include usage examples

  Scenario: Initialize a project with path parameter
    When I run the command "devsynth init --path ./my-custom-project"
    Then a new project should be created at "./my-custom-project"
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Initialize a project with language and root options
    When I run the command "devsynth init --project-root . --language python"
    Then a new project should be created at "."
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Initialize a project with directories and goals
    When I run the command "devsynth init --project-root . --language python --source-dirs src --test-dirs tests --docs-dirs docs --extra-languages javascript --goals demo"
    Then a new project should be created at "."
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Generate specifications with custom requirements file
    When I run the command "devsynth spec --requirements-file custom-requirements.md"
    Then the system should process the "custom-requirements.md" file
    And generate specifications based on the requirements
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Generate tests with custom specification file
    When I run the command "devsynth test --spec-file custom-specs.md"
    Then the system should process the "custom-specs.md" file
    And generate tests based on the specifications
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Generate code without parameters
    When I run the command "devsynth code"
    Then the system should generate code based on the tests
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Run with specific target
    When I run the command "devsynth run-pipeline --target unit-tests"
    Then the system should execute the "unit-tests" target
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Configure with key and value
    When I run the command "devsynth config --key model --value gpt-4"
    Then the system should update the configuration
    And set "model" to "gpt-4"
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: View configuration for specific key
    When I run the command "devsynth config --key model"
    Then the system should display the value for "model"
    And the workflow should execute successfully

  Scenario: View all configuration
    When I run the command "devsynth config"
    Then the system should display all configuration settings
    And the workflow should execute successfully

  Scenario: Handle invalid command
    When I run the command "devsynth invalid-command"
    Then the system should display the help information
    And indicate that the command is not recognized

  Scenario: Run an EDRR cycle from a manifest
    When I run the command "devsynth edrr-cycle sample_manifest.yaml"
    Then the workflow should execute successfully
    And the system should display a success message
