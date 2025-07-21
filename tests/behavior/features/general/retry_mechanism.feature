
Feature: Retry Mechanism with Exponential Backoff
  As a developer
  I want to have a retry mechanism with exponential backoff
  So that I can handle transient errors gracefully

  Scenario: Successful retry after transient errors
    Given a function that fails 2 times and then succeeds
    When I apply the retry decorator with max_retries=3 and initial_delay=0.1
    And I call the decorated function
    Then the function should be called 3 times
    And the final result should be successful

  Scenario: Failure after maximum retries
    Given a function that always fails
    When I apply the retry decorator with max_retries=3 and initial_delay=0.1
    And I call the decorated function
    Then the function should be called 4 times
    And the function should raise an exception

  Scenario: Exponential backoff with jitter
    Given a function that always fails
    When I apply the retry decorator with max_retries=3, initial_delay=1.0, and jitter=True
    And I call the decorated function
    Then the function should be called 4 times
    And the delays between retries should follow exponential backoff with jitter

  Scenario: Callback function is called on each retry
    Given a function that always fails
    When I apply the retry decorator with max_retries=3, initial_delay=0.1, and a callback function
    And I call the decorated function
    Then the function should be called 4 times
    And the callback function should be called 3 times
    And the callback function should receive the correct arguments

  Scenario: Only specified exceptions trigger retries
    Given a function that raises different types of exceptions
    When I apply the retry decorator with max_retries=3, initial_delay=0.1, and retryable_exceptions=(ValueError,)
    And I call the decorated function
    Then the function should be called 2 times
    And the function should raise a TypeError

  Scenario: Deterministic backoff without jitter
    Given a function that always fails
    When I apply the retry decorator with max_retries=3, initial_delay=1.0, and jitter=False
    And I call the decorated function
    Then the function should be called 4 times
    And the delays between retries should follow deterministic exponential backoff
