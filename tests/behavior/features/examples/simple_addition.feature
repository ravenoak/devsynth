
Feature: Simple Addition
  As a user
  I want to add two numbers
  So that I can get their sum

  Scenario: Add two numbers
    Given I have the numbers 1 and 2
    When I add them together
    Then the result should be 3
