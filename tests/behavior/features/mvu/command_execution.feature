Feature: MVU shell command execution
  As a developer
  I want MVU to run shell commands within a traceable session
  So that MVU workflows can execute tasks

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Execute a shell command through MVU
    When I run the command "devsynth mvu exec echo hello"
    Then the command should succeed
    And the output should contain "hello"
