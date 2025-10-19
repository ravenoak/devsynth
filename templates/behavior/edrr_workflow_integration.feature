Feature: EDRR Workflow Integration
  As a developer using DevSynth
  I want to use EDRR principles across all workflows
  So that I can benefit from a consistent, iterative approach to development

  Background:
    Given the DevSynth system is initialized
    And the EDRR methodology is configured

  Scenario: Apply EDRR to planning workflow
    When I initiate a planning task
    Then the system should apply the Expand phase to generate multiple approaches
    And the system should apply the Differentiate phase to evaluate and select approaches
    And the system should apply the Refine phase to detail the selected approach
    And the system should apply the Retrospect phase to review and learn from the process

  Scenario: Apply EDRR to specification workflow
    When I initiate a specification task
    Then the system should apply the Expand phase to explore requirements
    And the system should apply the Differentiate phase to prioritize requirements
    And the system should apply the Refine phase to formalize the specifications
    And the system should apply the Retrospect phase to validate the specifications

  Scenario: Apply EDRR to coding workflow
    When I initiate a coding task
    Then the system should apply the Expand phase to explore implementation options
    And the system should apply the Differentiate phase to select the best implementation
    And the system should apply the Refine phase to optimize the code
    And the system should apply the Retrospect phase to review the code quality

  Scenario: Tag memory items with EDRR phases
    When I store information during an EDRR workflow
    Then each memory item should be tagged with its corresponding EDRR phase
    And I should be able to query memory items by EDRR phase
    And the system should maintain the relationship between items across phases

  Scenario: Structure agent deliberation as EDRR cycles
    When agents collaborate on a task
    Then their deliberation should follow the EDRR pattern
    And each agent should contribute to each phase based on its expertise
    And the system should track progress through the EDRR cycle
    And the final output should reflect the complete EDRR process

  Scenario: Use EDRR for project analysis
    When I analyze a project
    Then the system should expand to identify all relevant components
    And the system should differentiate to focus on high-impact areas
    And the system should refine to generate specific recommendations
    And the system should retrospect to evaluate the analysis process
