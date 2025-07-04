
Feature: Code Command
  As a developer
  I want to generate code from tests
  So that I can implement functionality that passes the tests

  Scenario: Generate code from tests
    When I run the command "devsynth code"
    Then the code command should be executed
