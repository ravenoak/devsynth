Feature: Doctor command
  As a developer
  I want to verify my environment configuration
  So that DevSynth can run properly

  Scenario: Run doctor with valid configuration
    Given valid environment configuration
    When I run the command "devsynth doctor"
    Then the system should display a success message
