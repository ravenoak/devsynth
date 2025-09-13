# Related issue: ../../../../docs/specifications/per_error_retry_policies.md
Feature: Per-error retry policies
  As a developer
  I want retries to honour per-error policies
  So that transient and fatal errors are handled appropriately

  Scenario: policy prevents retry
    Given a function with a retry policy disabling retries
    When the function raises a disallowed error
    Then the retry loop aborts immediately

  Scenario: policy applies to subclass exceptions
    Given a retry policy defined for a base exception type
    When a subclass of that exception is raised
    Then the policy governs the retry attempts

  Scenario: policy emits metrics
    Given metrics collection is enabled
    When a retry policy suppresses retries
    Then a policy metric is recorded
