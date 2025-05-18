
Feature: Workflow Execution
  As a developer
  I want the DevSynth workflow system to orchestrate tasks
  So that the development process is automated and efficient

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Execute a complete workflow without errors
    When I run the command "devsynth spec --requirements-file requirements.md"
    Then the workflow should be created with a unique ID
    And the workflow should execute all steps in sequence
    And each step should be marked as completed
    And the workflow should complete successfully
    And the system should display a success message

  Scenario: Handle errors in workflow execution
    Given the requirements file "invalid-requirements.md" does not exist
    When I run the command "devsynth spec --requirements-file invalid-requirements.md"
    Then the workflow should be created with a unique ID
    And the workflow should fail during execution
    And the system should display an appropriate error message
    And the workflow status should be marked as failed

  Scenario: Resume a workflow after human intervention
    Given a workflow that requires human intervention
    When I run a command that triggers this workflow
    Then the workflow should pause at the step requiring intervention
    And the system should prompt for human input
    And when I provide the required input
    Then the workflow should resume execution
    And complete successfully
    And the system should display a success message

  Scenario: Execute multiple workflows in sequence
    When I run the command "devsynth spec --requirements-file requirements.md"
    And the workflow completes successfully
    And I run the command "devsynth test --spec-file specs.md"
    Then both workflows should execute successfully
    And the system should maintain the correct state between workflows
    And the system should display success messages for both commands

  Scenario: Handle workflow with long-running steps
    When I run a command that triggers a workflow with long-running steps
    Then the system should provide progress updates
    And the workflow should execute all steps
    And complete successfully
    And the system should display a success message
