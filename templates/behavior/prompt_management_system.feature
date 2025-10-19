Feature: DPSy-AI Prompt Management System
  As a developer using DevSynth
  I want to use the DPSy-AI prompt management system
  So that I can benefit from optimized prompts, structured reflection, and improved explainability

  Background:
    Given the DevSynth system is initialized
    And the DPSy-AI prompt management system is configured

  Scenario: Store and retrieve prompt templates
    When I create a prompt template with name "code_generation"
    And I add template text with placeholders for variables
    Then the template should be stored in the prompt library
    And I should be able to retrieve the template by name
    And the retrieved template should match the original

  Scenario: Use prompt templates with variable substitution
    Given I have a prompt template with variables
    When I use the template with specific variable values
    Then the system should substitute the variables in the template
    And the resulting prompt should contain the provided values
    And the prompt should be properly formatted

  Scenario: Version prompt templates
    Given I have a prompt template named "code_review"
    When I create a new version of the template with improvements
    Then both versions should be stored in the system
    And I should be able to retrieve a specific version
    And the system should default to the latest version

  Scenario: Structured reflection on prompt responses
    When an agent uses a prompt to generate a response
    Then the system should automatically trigger a reflection step
    And the reflection should evaluate the quality of the response
    And the reflection results should be stored for future optimization

  Scenario: Dynamic prompt tuning
    Given I have multiple variants of a prompt template
    When the system uses these variants for similar tasks
    Then it should track the effectiveness of each variant
    And it should learn which variants perform better for specific contexts
    And it should prioritize better-performing variants in future tasks

  Scenario: Enhanced explainability with rationales
    When an agent generates a response using the prompt system
    Then the response should include a rationale for the decision
    And the rationale should explain the agent's reasoning process
    And the rationale should be stored alongside the response

  Scenario: Prompt efficacy feedback loop
    Given an agent has used a prompt template multiple times
    When I request an analysis of the template's performance
    Then the system should provide metrics on its effectiveness
    And it should suggest potential improvements to the template
    And I should be able to apply these improvements to create a new version
