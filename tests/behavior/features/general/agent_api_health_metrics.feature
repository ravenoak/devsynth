Feature: Agent API Health and Metrics
  As a DevOps engineer
  I want to monitor the health and metrics of the Agent API
  So that I can ensure it's functioning correctly and track its usage

  Scenario: Check API health
    Given the Agent API server is running
    When I GET /health
    Then the response status code should be 200
    And the response should contain "status" with value "ok"

  Scenario: Check API health with authentication
    Given the Agent API server is running with authentication enabled
    When I GET /health with a valid token
    Then the response status code should be 200
    And the response should contain "status" with value "ok"

  Scenario: Check API health with invalid authentication
    Given the Agent API server is running with authentication enabled
    When I GET /health with an invalid token
    Then the response status code should be 401
    And the response should contain an error message

  Scenario: Get API metrics
    Given the Agent API server is running
    When I GET /metrics
    Then the response status code should be 200
    And the response should contain "request_count"
    And the response should contain "endpoint_latency"
    And the response should contain "error_count"

  Scenario: Get API metrics with authentication
    Given the Agent API server is running with authentication enabled
    When I GET /metrics with a valid token
    Then the response status code should be 200
    And the response should contain "request_count"
    And the response should contain "endpoint_latency"
    And the response should contain "error_count"

  Scenario: Get API metrics with invalid authentication
    Given the Agent API server is running with authentication enabled
    When I GET /metrics with an invalid token
    Then the response status code should be 401
    And the response should contain an error message
