Feature: Prompt Management with DPSy-AI
  As a developer
  I want to use a centralized prompt management system
  So that I can ensure consistent, optimized prompts across all agents

  Background:
    Given the DPSy-AI prompt management system is initialized

  Scenario: Register a prompt template
    When I register a prompt template with the following details:
      | name        | description                | template_text                                |
      | code_review | Template for code reviews | Review the following code:\n\n{code}\n\n{instructions} |
    Then the prompt template should be stored in the prompt manager
    And I should be able to retrieve the template by name

  Scenario: Use a prompt template with an agent
    Given a prompt template named "code_review" exists
    And a Code Agent is initialized
    When the agent uses the "code_review" template with the following variables:
      | code         | def add(a, b): return a + b |
      | instructions | Check for bugs and suggest improvements |
    Then the agent should receive the fully rendered prompt
    And the prompt usage should be logged for optimization

  Scenario: Prompt template versioning
    Given a prompt template named "code_review" exists
    When I update the template with a new version:
      | template_text | Review this code carefully:\n\n{code}\n\n{instructions}\n\nFocus on: security, performance, readability |
    Then both versions of the template should be available
    And the latest version should be used by default
    And I should be able to specify which version to use

  Scenario: Prompt efficacy tracking
    Given a prompt template named "code_review" has been used multiple times
    When I request efficacy metrics for the template
    Then I should receive statistics on its performance
    And recommendations for potential improvements

  Scenario: Structured reflection after prompt response
    Given a prompt template named "code_review" exists
    When an agent uses the template and receives a response
    Then a reflection step should be triggered
    And the reflection results should be stored for future optimization

  Scenario: Dynamic prompt adjustment based on feedback
    Given a prompt template named "code_review" exists
    And the prompt auto-tuner is enabled
    When the template is used multiple times with varying feedback scores
    Then the system should automatically adjust the prompt template
    And the adjusted template should incorporate successful patterns
    And the adjusted template should avoid unsuccessful patterns

  Scenario: Track prompt variant performance
    Given multiple variants of a prompt template exist:
      | variant_name | description                   |
      | variant_1    | Original version              |
      | variant_2    | More detailed instructions    |
      | variant_3    | Simplified instructions       |
    When each variant is used in similar contexts
    Then the system should track performance metrics for each variant
    And the system should identify the best-performing variant
    And the best-performing variant should be recommended for future use

  Scenario: Generate new prompt variants through mutation
    Given a prompt template named "code_review" exists with performance data
    When I request the auto-tuner to generate new variants
    Then the system should create mutated versions of the template
    And each mutation should modify different aspects of the prompt
    And the mutations should be based on historical performance data

  Scenario: Generate new prompt variants through recombination
    Given multiple prompt templates exist with performance data
    When I request the auto-tuner to generate recombined variants
    Then the system should create new templates by combining successful elements
    And the recombined templates should preserve the core functionality
    And the recombined templates should be added to the available templates

  Scenario: Automatic A/B testing of prompt variants
    Given multiple variants of a prompt template exist
    When I enable A/B testing for the template
    Then the system should automatically distribute usage across variants
    And the system should collect performance metrics for each variant
    And after sufficient data is collected, the system should select the best variant
    And the best variant should become the new default

  Scenario: Continuous prompt optimization cycle
    Given the prompt auto-tuner is enabled for a template
    When the template is used in production for a period of time
    Then the system should continuously generate and test new variants
    And the system should progressively improve template performance
    And the system should maintain a history of all optimization steps
