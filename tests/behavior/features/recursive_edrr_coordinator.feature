Feature: Recursive EDRR Coordinator
  As a coordinator maintainer
  I want nested cycles to remain bounded and auditable
  So that recursive refinement respects the configured limits

  Background:
    Given the EDRR coordinator is initialized with recursion support
    And the memory system is available
    And the WSDE team is available
    And the AST analyzer is available
    And the prompt manager is available
    And the documentation manager is available

  Scenario: Create a micro cycle within the Expand phase
    When I start the EDRR cycle with a task to "implement a complex feature"
    Then the coordinator should enter the "Expand" phase
    When I create a micro-EDRR cycle for "brainstorm approaches" within the "Expand" phase
    Then the micro cycle should be created successfully
    And the micro cycle should have the parent cycle ID set correctly
    And the micro cycle should have recursion depth of 1
    And the micro cycle should be tracked as a child of the parent cycle

  Scenario: Enforce recursion depth limits
    When I start the EDRR cycle with a task to "implement a feature"
    And I create a micro-EDRR cycle for "level 1 task" within the "Expand" phase
    And I create a micro-EDRR cycle for "level 2 task" within the "Expand" phase of the "level 1 task" cycle
    And I create a micro-EDRR cycle for "level 3 task" within the "Expand" phase of the "level 2 task" cycle
    Then attempting to create another micro cycle should fail due to recursion depth limits
