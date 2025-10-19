Feature: WebUI Command Execution
  As a developer
  I want to use the DevSynth WebUI command
  So that I can access the graphical interface for managing my development workflow

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Launch the WebUI
    When I run the command "devsynth webui"
    Then the system should launch the Streamlit WebUI
    And the workflow should execute successfully
    And the system should display a success message

  Scenario: Handle WebUI launch error
    Given the Streamlit WebUI module is unavailable
    When I run the command "devsynth webui"
    Then the system should display an error message
    And the error message should indicate the WebUI could not be launched

  Scenario: WebUI contains all required pages
    When I run the command "devsynth webui"
    Then the system should launch the Streamlit WebUI
    And the WebUI should contain the following pages:
      | Onboarding        |
      | Requirements      |
      | Analysis          |
      | Synthesis         |
      | EDRR Cycle        |
      | Alignment         |
      | Alignment Metrics |
      | Inspect Config    |
      | Validate Manifest |
      | Validate Metadata |
      | Test Metrics      |
      | Generate Docs     |
      | Ingest            |
      | API Spec          |
      | Refactor          |
      | Web App           |
      | Serve             |
      | DB Schema         |
      | Config            |
      | Doctor            |
      | Diagnostics       |
