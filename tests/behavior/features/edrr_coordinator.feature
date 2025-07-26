Feature: EDRR Coordinator
  As a developer
  I want a coordinator that orchestrates the flow between components according to the EDRR pattern
  So that all features work together in a cohesive and functional whole

  Background:
    Given the EDRR coordinator is initialized
    And the memory system is available
    And the WSDE team is available
    And the AST analyzer is available
    And the prompt manager is available
    And the documentation manager is available

  Scenario: Coordinate components through the Expand phase
    When I start the EDRR cycle with a task to "analyze a Python file"
    Then the coordinator should enter the "Expand" phase
    And the coordinator should store the task in memory with EDRR phase "Expand"
    And the WSDE team should be instructed to brainstorm approaches
    And the AST analyzer should be used to analyze the file structure
    And the prompt manager should provide templates for the "Expand" phase
    And the documentation manager should retrieve relevant documentation
    And the results should be stored in memory with EDRR phase "Expand"

  Scenario: Coordinate components through the Differentiate phase
    Given the "Expand" phase has completed for a task
    When the coordinator progresses to the "Differentiate" phase
    Then the coordinator should store the phase transition in memory
    And the WSDE team should be instructed to evaluate and compare approaches
    And the AST analyzer should be used to evaluate code quality
    And the prompt manager should provide templates for the "Differentiate" phase
    And the documentation manager should retrieve best practices documentation
    And the results should be stored in memory with EDRR phase "Differentiate"

  Scenario: Coordinate components through the Refine phase
    Given the "Differentiate" phase has completed for a task
    When the coordinator progresses to the "Refine" phase
    Then the coordinator should store the phase transition in memory
    And the WSDE team should be instructed to implement the selected approach
    And the AST analyzer should be used to apply code transformations
    And the prompt manager should provide templates for the "Refine" phase
    And the documentation manager should retrieve implementation examples
    And the results should be stored in memory with EDRR phase "Refine"

  Scenario: Coordinate components through the Retrospect phase
    Given the "Refine" phase has completed for a task
    When the coordinator progresses to the "Retrospect" phase
    Then the coordinator should store the phase transition in memory
    And the WSDE team should be instructed to evaluate the implementation
    And the AST analyzer should be used to verify code quality
    And the prompt manager should provide templates for the "Retrospect" phase
    And the documentation manager should retrieve evaluation criteria
    And the results should be stored in memory with EDRR phase "Retrospect"
    And a final report should be generated summarizing the entire EDRR cycle

  Scenario: Start EDRR cycle from a manifest file
    Given a valid EDRR manifest file exists
    When I start the EDRR cycle from the manifest file
    Then the coordinator should parse the manifest successfully
    And the coordinator should enter the "Expand" phase
    And the coordinator should use the phase instructions from the manifest
    And the coordinator should use the phase templates from the manifest
    And the coordinator should track phase dependencies
    And the coordinator should monitor execution progress

  Scenario: Track comprehensive logging and traceability
    Given the EDRR coordinator is initialized with enhanced logging
    When I complete a full EDRR cycle with a task to "implement a feature"
    Then the coordinator should generate detailed execution traces
    And the execution traces should include phase-specific metrics
    And the execution traces should include status tracking for each phase
    And the execution traces should include comprehensive metadata
    And I should be able to retrieve the full execution history
    And I should be able to analyze performance metrics for each phase

  Scenario: Micro cycle creation within the Expand phase
    Given the EDRR coordinator is initialized with recursion support
    And the memory system is available
    And the WSDE team is available
    And the AST analyzer is available
    And the prompt manager is available
    And the documentation manager is available
    When I start the EDRR cycle with a task to "implement a complex feature"
    And I create a micro cycle for "brainstorm approaches" in phase "Expand"
    Then the micro cycle should have recursion depth 1
    And the parent cycle should include the micro cycle
