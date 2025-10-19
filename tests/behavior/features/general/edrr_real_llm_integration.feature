Feature: EDRR Integration with Real LLM Providers
  As a developer
  I want to use the EDRR framework with real LLM providers
  So that I can leverage advanced language models for complex tasks

  @requires_llm_provider
  Scenario: Run EDRR cycle with real LLM for simple task
    Given an initialized EDRR coordinator with real LLM provider
    When I start an EDRR cycle for "Create a function to calculate the factorial of a number"
    And I progress through all EDRR phases
    Then the cycle should complete successfully
    And the final solution should contain a factorial function
    And the solution should handle edge cases

  @requires_llm_provider
  Scenario: Run EDRR cycle with real LLM for complex project
    Given an initialized EDRR coordinator with real LLM provider
    And a sample Flask application with code quality issues
    When I start an EDRR cycle to "Analyze and improve the Flask application"
    And I progress through all EDRR phases
    Then the cycle should complete successfully
    And the final solution should address validation issues
    And the final solution should include error handling
    And the final solution should follow Flask best practices

  @requires_llm_provider
  Scenario: EDRR with real LLM handles memory integration
    Given an initialized EDRR coordinator with real LLM provider
    And a configured graph memory system
    When I start an EDRR cycle for "Create a data processing pipeline"
    And I progress through all EDRR phases
    Then the cycle should complete successfully
    And the memory system should store phase results correctly
    And the final solution should reference previous phase insights
