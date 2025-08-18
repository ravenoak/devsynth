Feature: Simple addition input validation
  The add function should reject non-numeric inputs.

  Scenario: adding string inputs raises a TypeError
    Given I have non-numeric inputs
    When I try to add them
    Then a TypeError is raised
