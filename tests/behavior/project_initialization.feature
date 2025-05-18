
Feature: Project Initialization
  As a developer
  I want to initialize a new DevSynth project
  So that I can start developing software with AI assistance

  Scenario: Initialize a new project with default settings
    Given the DevSynth CLI is installed
    When I run the command "devsynth init --name my-project"
    Then a new project directory "my-project" should be created
    And the project should have the default structure
    And a configuration file should be created with default settings

  Scenario: Initialize a project with custom settings
    Given the DevSynth CLI is installed
    When I run the command "devsynth init --name custom-project --template web-app"
    Then a new project directory "custom-project" should be created
    And the project should have the web-app template structure
    And a configuration file should be created with web-app template settings
