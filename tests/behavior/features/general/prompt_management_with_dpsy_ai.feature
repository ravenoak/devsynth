Feature: Prompt Management with DPSy-AI
  As a developer
  I want to manage prompt templates centrally
  So that agents share optimized, auditable prompts

  Background:
    Given the DPSy-AI prompt management system is initialized

  Scenario: Register and retrieve a prompt template
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
