Feature: Recursive EDRR Coordinator
  As a developer
  I want a coordinator that implements the EDRR pattern recursively
  So that each macro phase can contain its own nested micro-EDRR cycles

  Background:
    Given the EDRR coordinator is initialized with recursion support
    And the memory system is available
    And the WSDE team is available
    And the AST analyzer is available
    And the prompt manager is available
    And the documentation manager is available

  Scenario: Create micro-EDRR cycles within the Expand phase
    When I start the EDRR cycle with a task to "implement a complex feature"
    Then the coordinator should enter the "Expand" phase
    When I create a micro-EDRR cycle for "brainstorm approaches" within the "Expand" phase
    Then the micro cycle should be created successfully
    And the micro cycle should have the parent cycle ID set correctly
    And the micro cycle should have recursion depth of 1
    And the micro cycle should be tracked as a child of the parent cycle
    When the micro cycle executes its "Expand" phase
    Then the micro cycle should generate ideas for "brainstorm approaches"
    And the micro cycle results should be integrated into the parent cycle

  Scenario: Create micro-EDRR cycles within the Differentiate phase
    Given the "Expand" phase has completed for a task
    When the coordinator progresses to the "Differentiate" phase
    And I create a micro-EDRR cycle for "compare approaches" within the "Differentiate" phase
    Then the micro cycle should be created successfully
    And the micro cycle should have the parent cycle ID set correctly
    And the micro cycle should have recursion depth of 1
    When the micro cycle executes its "Expand" phase
    And the micro cycle progresses to the "Differentiate" phase
    Then the micro cycle should evaluate options for "compare approaches"
    And the micro cycle results should be integrated into the parent cycle

  Scenario: Create micro-EDRR cycles within the Refine phase
    Given the "Differentiate" phase has completed for a task
    When the coordinator progresses to the "Refine" phase
    And I create a micro-EDRR cycle for "implement solution" within the "Refine" phase
    Then the micro cycle should be created successfully
    And the micro cycle should have the parent cycle ID set correctly
    And the micro cycle should have recursion depth of 1
    When the micro cycle completes a full EDRR cycle
    Then the micro cycle should produce an implementation for "implement solution"
    And the micro cycle results should be integrated into the parent cycle

  Scenario: Create micro-EDRR cycles within the Retrospect phase
    Given the "Refine" phase has completed for a task
    When the coordinator progresses to the "Retrospect" phase
    And I create a micro-EDRR cycle for "extract learnings" within the "Retrospect" phase
    Then the micro cycle should be created successfully
    And the micro cycle should have the parent cycle ID set correctly
    And the micro cycle should have recursion depth of 1
    When the micro cycle completes a full EDRR cycle
    Then the micro cycle should produce learnings for "extract learnings"
    And the micro cycle results should be integrated into the parent cycle

  Scenario: Enforce recursion depth limits
    When I start the EDRR cycle with a task to "implement a feature"
    And I create a micro-EDRR cycle for "level 1 task" within the "Expand" phase
    And I create a micro-EDRR cycle for "level 2 task" within the "Expand" phase of the "level 1 task" cycle
    And I create a micro-EDRR cycle for "level 3 task" within the "Expand" phase of the "level 2 task" cycle
    Then attempting to create another micro cycle should fail due to recursion depth limits

  Scenario: Apply granularity threshold checks
    When I start the EDRR cycle with a task to "implement a feature"
    Then creating a micro cycle for a very granular task should be prevented
    But creating a micro cycle for a complex task should be allowed

  Scenario: Apply cost-benefit analysis
    When I start the EDRR cycle with a task to "implement a feature"
    Then creating a micro cycle for a high-cost low-benefit task should be prevented
    But creating a micro cycle for a low-cost high-benefit task should be allowed

  Scenario: Apply quality threshold monitoring
    When I start the EDRR cycle with a task to "implement a feature"
    Then creating a micro cycle for a task that already meets quality thresholds should be prevented
    But creating a micro cycle for a task that needs quality improvement should be allowed

  Scenario: Apply resource limits
    When I start the EDRR cycle with a task to "implement a feature"
    Then creating a micro cycle for a resource-intensive task should be prevented
    But creating a micro cycle for a lightweight task should be allowed

  Scenario: Support human judgment override
    When I start the EDRR cycle with a task to "implement a feature"
    Then creating a micro cycle with human override to terminate should be prevented
    But creating a micro cycle with human override to continue should be allowed
