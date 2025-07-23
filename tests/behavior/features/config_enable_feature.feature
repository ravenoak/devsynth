Feature: Enable optional features
  As a developer
  I want to enable DevSynth features
  So that additional functionality is activated

  Scenario: Enable code generation feature
    Given a project configuration without the "code_generation" feature enabled
    When I run the command "devsynth config enable-feature code_generation"
    Then the configuration should mark "code_generation" as enabled
    And the system should display a success message
