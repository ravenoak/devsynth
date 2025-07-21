Feature: WebUI Doctor
  As a developer
  I want to validate configuration from the WebUI
  So that I can fix issues easily

  Background:
    Given the WebUI is initialized

  Scenario: Run doctor diagnostics
    When I navigate to "Doctor"
    Then the doctor command should be executed
