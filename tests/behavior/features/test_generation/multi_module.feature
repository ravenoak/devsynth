Feature: Multi-module test generation

  Scenario: Generate integration tests for multiple modules
    Given a project with multiple modules
    When the TestAgent generates integration tests
    Then tests are scaffolded for each module
