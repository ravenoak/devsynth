Feature: DevSynth Doctor
  As a developer
  I want helpful feedback when configuration is missing
  So that I can onboard my project correctly

  Background:
    Given the DevSynth CLI is installed
    And I have a valid DevSynth project

  Scenario: Suggest initialization when config is absent
    Given no DevSynth configuration file in the project
    When I run the command "devsynth doctor"
    Then the output should mention that no project configuration was found
    And the output should include onboarding hints
