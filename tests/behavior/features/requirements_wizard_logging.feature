Feature: Requirements Wizard Logging
  As a maintainer auditing the wizard
  I want structured log entries to capture user choices
  So that compliance evidence and configuration stay synchronized

  Scenario: Log entries and configuration capture the chosen priority
    Given logging is configured for the requirements wizard
    When I run the requirements wizard with priority "high"
    Then the log should include the priority "high"
    And the configuration file should record priority "high"
