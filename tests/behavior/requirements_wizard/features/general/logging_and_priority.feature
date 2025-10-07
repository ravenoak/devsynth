Feature: Requirements wizard logging and priority persistence
  As a developer
  I want the wizard to log user choices and store the selected priority
  So that sessions are auditable and configuration reflects decisions

  Scenario: Logging includes priority and configuration saves it
    Given logging is configured for the requirements wizard
    When I run the requirements wizard with priority "high"
    Then the log should include the priority "high"
    And the configuration file should record priority "high"
