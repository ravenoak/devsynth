Feature: Web Application Generation
  As a developer using DevSynth
  I want to generate web applications
  So that I can quickly create web-based projects

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  @webapp-generation
  Scenario: Generate a Flask web application with default parameters
    When I run the command "devsynth webapp"
    Then the system should generate a Flask web application
    And the application should be created in the current directory
    And the application should be named "webapp"
    And the output should indicate that the application was generated
    And the workflow should execute successfully

  @webapp-generation
  Scenario: Generate a web application with custom framework
    When I run the command "devsynth webapp --framework fastapi"
    Then the system should generate a FastAPI web application
    And the application should be created in the current directory
    And the application should be named "webapp"
    And the output should indicate that the application was generated
    And the workflow should execute successfully

  @webapp-generation
  Scenario: Generate a web application with custom name
    When I run the command "devsynth webapp --name myapp"
    Then the system should generate a Flask web application
    And the application should be created in the current directory
    And the application should be named "myapp"
    And the output should indicate that the application was generated
    And the workflow should execute successfully

  @webapp-generation
  Scenario: Generate a web application in a custom location
    When I run the command "devsynth webapp --path ./apps"
    Then the system should generate a Flask web application
    And the application should be created in the "./apps" directory
    And the application should be named "webapp"
    And the output should indicate that the application was generated
    And the workflow should execute successfully

  @webapp-generation
  Scenario: Generate a web application with all custom parameters
    When I run the command "devsynth webapp --framework django --name myproject --path ./projects"
    Then the system should generate a Django web application
    And the application should be created in the "./projects" directory
    And the application should be named "myproject"
    And the output should indicate that the application was generated
    And the workflow should execute successfully

  @webapp-generation
  Scenario: Handle unsupported framework
    When I run the command "devsynth webapp --framework unsupported"
    Then the system should display an error message
    And the error message should indicate that the framework is not supported
    And the workflow should not execute successfully
