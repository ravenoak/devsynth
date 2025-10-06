Feature: Generated tests fail when requirements are unmet
  As a developer
  I want scaffolded tests to execute and fail until implemented
  So that unmet requirements are visible early

  Scenario: Run scaffolded tests without implementations
    Given integration scenarios are defined
    When the generated tests are executed
    Then the test run reports missing implementation failures
