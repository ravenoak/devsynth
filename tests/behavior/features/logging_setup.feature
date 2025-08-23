Feature: Logging Setup Utilities
  As a developer
  I want structured logging helpers
  So that logs include request context

  Scenario: JSON formatter includes request id
    Given a request id is set
    When a log message is emitted
    Then the JSON output contains the request id
