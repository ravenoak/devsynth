Feature: Per-error retry policies
  As a developer
  I want retries to honour per-error policies
  So that transient and fatal errors are handled appropriately

  Scenario: policy prevents retry
    Given a function with a retry policy disabling retries
    When the function raises a disallowed error
    Then the retry loop aborts immediately
