Feature: Doctor Command
  As a developer
  I want to validate environment configuration
  So that I can fix issues before running other commands

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Warn about invalid environment configuration
    Given a project with invalid environment configuration
    When I run the command "devsynth doctor"
    Then the system should display a warning message
    And the output should indicate configuration errors

  Scenario: Validate existing environment configuration
    Given valid environment configuration
    When I run the command "devsynth doctor"
    Then the system should display a success message

  Scenario: Validate configuration using the check alias
    Given valid environment configuration
    When I run the command "devsynth check"
    Then the system should display a success message

  Scenario: Warn when essential environment variables are missing
    Given essential environment variables are missing
    When I run the command "devsynth doctor"
    Then the output should mention the missing variables

  Scenario: Warn about invalid YAML files in the config directory
    Given a config directory with invalid YAML
    When I run the command "devsynth doctor"
    Then the system should display a warning message
    And the output should indicate configuration errors

  Scenario: Detect invalid YAML syntax in devsynth.yml
    Given a devsynth.yml file with invalid YAML syntax
    When I run the command "devsynth doctor"
    Then the system should display a warning message
    And the output should indicate configuration errors

  Scenario: Warn about unsupported configuration keys
    Given a devsynth.yml file with unsupported configuration keys
    When I run the command "devsynth doctor"
    Then the system should display a warning message
    And the output should indicate configuration errors

  Scenario: Warn when .env file is missing
    Given no .env file exists in the project
    When I run the command "devsynth doctor"
    Then the system should display a warning message
    And the output should mention the missing .env file
