Feature: Micro EDRR Cycle
  As a developer
  I want to create micro EDRR cycles within a parent cycle
  So that complex tasks can be broken down recursively

  Scenario: Create a micro cycle from the expand phase
    Given an initialized EDRR coordinator
    And I register micro cycle monitoring hooks
    When I start an EDRR cycle for "implement feature"
    And I create a micro cycle for "sub task" in phase "Expand"
    Then the micro cycle should have recursion depth 1
    And the parent cycle should include the micro cycle
    And the hooks should record the micro cycle lifecycle
