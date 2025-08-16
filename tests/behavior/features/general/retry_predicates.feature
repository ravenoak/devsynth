Feature: Retry Predicates for HTTP status codes
  As a developer
  I want to retry operations based on result predicates
  So that transient server errors are handled transparently

  Scenario: Retry on HTTP 503 status code
    Given an HTTP request function that returns status 503 then 200
    When I apply the retry decorator with a predicate for status>=500 and jitter=False
    And I call the decorated function
    Then the function should be called 2 times
    And the final result should be successful
