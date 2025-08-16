Feature: Test Agent executes generated tests
  As a developer
  I want the TestAgent to run generated tests
  So that unmet requirements cause test failures

  Scenario: Run generated tests with unmet requirement
    Given a generated test referencing an unmet requirement
    When the TestAgent runs the test suite
    Then the test run should fail
