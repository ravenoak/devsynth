Feature: Logger Configuration
  As a developer
  I want a configured logger
  So that logs are formatted consistently

  Scenario: Normalize exc_info
    Given an exception instance
    When I log with exc_info
    Then the logger records the stack trace without error
