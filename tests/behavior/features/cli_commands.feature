
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

  Scenario: Initialize a project with goals
    When I run the command "devsynth init --project-root . --language python --goals demo"
    Then a new project should be created at "."
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Initialize interactively
    When I run the command "devsynth init"
    Then the workflow should execute successfully
    And the system should display a success message

  Scenario: Run the wizard via command line
    When I run the command "devsynth init --wizard"
    Then the workflow should execute successfully
    And the system should display a success message

  Scenario: Generate specifications with custom requirements file
    When I run the command "devsynth inspect --requirements-file custom-requirements.md"
    Then the system should process the "custom-requirements.md" file
    And generate specifications based on the requirements
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Generate tests with custom specification file
    When I run the command "devsynth run-pipeline --spec-file custom-specs.md"
    Then the system should process the "custom-specs.md" file
    And generate tests based on the specifications
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Generate code without parameters
    When I run the command "devsynth refactor"
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

Scenario: Validate project configuration
  When I run the command "devsynth validate-manifest"
  Then the system should display a success message
  And the workflow should execute successfully

Scenario: Validate environment configuration
  Given a project with invalid environment configuration
  When I run the command "devsynth doctor"
  Then the system should display a warning message
  And the output should indicate configuration errors

Scenario: Serve API on custom port
  When I run the command "devsynth serve --port 8081"
  Then uvicorn should be called with host "0.0.0.0" and port 8081

Scenario: Doctor warns about missing environment variables
  Given essential environment variables are missing
  When I run the command "devsynth doctor"
  Then the system should display a warning message
  And the output should mention the missing variables

Scenario: Handle invalid manifest in EDRR cycle
  Given a project with an invalid manifest file
  When I run the command "devsynth edrr-cycle invalid_manifest.yaml"
  Then the system should display a warning message
  And the output should indicate configuration errors
