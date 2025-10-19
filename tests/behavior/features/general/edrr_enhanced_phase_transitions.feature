Feature: Enhanced EDRR Phase Transitions
  As a developer
  I want enhanced phase transition logic in the EDRR framework
  So that phase transitions are more intelligent, adaptive, and effective

  Background:
    Given the EDRR coordinator is initialized with enhanced phase transition features
    And the memory system is available
    And the WSDE team is available
    And the AST analyzer is available
    And the prompt manager is available
    And the documentation manager is available

  Scenario: Adaptive phase duration based on task complexity
    Given a task with complexity score of 8 out of 10
    When I start the EDRR cycle with this task
    Then the coordinator should allocate more time for complex phases
    And the "Expand" phase should have extended duration
    And the "Differentiate" phase should have extended duration
    And the phase durations should be proportional to the task complexity
    And the performance metrics should include phase duration adjustments

  Scenario: Phase-specific metrics for better monitoring
    Given the EDRR coordinator is configured to track detailed phase metrics
    When I complete a full EDRR cycle with a task
    Then the coordinator should generate phase-specific metrics
    And the metrics should include "quality score" for each phase
    And the metrics should include "completion percentage" for each phase
    And the metrics should include "resource utilization" for each phase
    And the metrics should include "effectiveness score" for each phase
    And these metrics should be stored in memory with appropriate metadata

  Scenario: Intelligent phase transition based on quality thresholds
    Given the EDRR coordinator is configured with quality thresholds
    When the "Expand" phase produces results below the quality threshold
    Then the coordinator should not automatically progress to the next phase
    And the coordinator should trigger additional processing in the current phase
    And the coordinator should log the quality issue and remediation attempt
    When the quality threshold is met after additional processing
    Then the coordinator should progress to the next phase
    And the phase transition should include quality metrics in the metadata

  Scenario: Dynamic phase transition criteria based on previous results
    Given the EDRR coordinator has completed several cycles
    When I start a new EDRR cycle with a similar task
    Then the coordinator should use historical data to optimize phase transitions
    And the phase transition criteria should be adjusted based on previous success patterns
    And the coordinator should prioritize strategies that were effective in similar tasks
    And the phase transition metadata should reference the historical data used

  Scenario: Phase transition with comprehensive context preservation
    Given the EDRR coordinator is in the "Expand" phase
    When the coordinator transitions to the "Differentiate" phase
    Then all relevant context from the previous phase should be preserved
    And the context should include all key insights from the "Expand" phase
    And the context should include all constraints identified in the "Expand" phase
    And the context should include all approaches generated in the "Expand" phase
    And the "Differentiate" phase should have access to this comprehensive context
