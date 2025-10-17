Feature: Requirements Wizard Logging
  As a developer
  I want detailed logs for the requirements wizard
  So that interactions can be audited and debugged

  Scenario: Log entries and configuration capture the chosen priority
    Given logging is configured for the requirements wizard
    When I run the requirements wizard with priority "high"
    Then the log should include the priority "high"
    And the configuration file should record priority "high"
