Feature: OpenRouter Integration
  As a DevSynth user
  I want to use OpenRouter as an LLM provider
  So that I can access multiple AI models through a unified API

  Background:
    Given I have configured DevSynth with OpenRouter provider
    And I have set OPENROUTER_API_KEY environment variable
    And I have a valid OpenRouter API key

  @requires_llm_provider
  Scenario: Basic text generation with OpenRouter using free-tier model
    Given I have configured OpenRouter with "google/gemini-flash-1.5" model
    When I call generate() with prompt "Hello, how are you?"
    Then I should receive a text response
    And the response should be a string
    And no exceptions should be raised
    And the response should contain helpful content

  @requires_llm_provider
  Scenario: Text generation with conversation context using free-tier model
    Given I have configured OpenRouter with "meta-llama/llama-3.1-8b-instruct" model
    And I have conversation context with system message "You are a helpful assistant"
    When I call generate_with_context() with prompt "What is the capital of France?" and context
    Then I should receive a text response
    And the response should be a string
    And the response should reference the context
    And no exceptions should be raised

  @requires_llm_provider
  Scenario: Embedding generation with OpenRouter
    Given I have configured OpenRouter with "text-embedding-ada-002" model
    When I call get_embedding() with text "The quick brown fox jumps over the lazy dog"
    Then I should receive an embedding vector
    And the embedding should be a list of floats
    And the embedding should have the expected dimensions
    And no exceptions should be raised

  @requires_llm_provider
  Scenario: Streaming generation with OpenRouter
    Given I have configured OpenRouter with "mistralai/mistral-7b-instruct" model
    When I call generate_stream() with prompt "Tell me a short story"
    Then I should receive an async generator
    And the generator should yield text chunks
    And each chunk should be a string
    And the complete response should form coherent text
    And no exceptions should be raised

  @requires_llm_provider
  Scenario: Error handling for invalid API key
    Given I have configured OpenRouter with invalid API key
    When I call generate() with prompt "Hello"
    Then I should receive LLMAuthenticationError
    And the error message should be descriptive
    And the error should contain helpful troubleshooting information

  @requires_llm_provider
  Scenario: Error handling for invalid model
    Given I have configured OpenRouter with "invalid-model-name" model
    When I call generate() with prompt "Hello"
    Then I should receive LLMModelError
    And the error message should suggest valid models
    And the error should contain helpful troubleshooting information

  @requires_llm_provider
  Scenario: Circuit breaker activation on repeated failures
    Given I have configured OpenRouter with a failing endpoint
    When I make 6 consecutive failing requests
    Then the circuit breaker should open
    And subsequent requests should fail immediately with circuit breaker error
    And the circuit breaker should attempt recovery after timeout

  @requires_llm_provider
  Scenario: Retry logic on transient failures
    Given I have configured OpenRouter with intermittent failures
    When I call generate() with prompt "Hello"
    Then the request should retry on transient errors
    And the request should succeed after retries
    And retry metrics should be recorded

  @requires_llm_provider
  Scenario: Free-tier model selection and validation
    Given I have multiple free-tier models available
    When I configure different free-tier models
    Then each model should work correctly
    And I should receive valid responses for each model
    And model-specific characteristics should be preserved

  @requires_llm_provider
  Scenario Outline: Free-tier model performance validation
    Given I have configured OpenRouter with "<model>" model
    When I call generate() with prompt "Write a haiku about programming"
    Then I should receive a text response within acceptable time
    And the response should be relevant to the prompt
    And the response quality should be acceptable for the model tier

    Examples:
      | model                          |
      | google/gemini-flash-1.5       |
      | meta-llama/llama-3.1-8b-instruct |
      | mistralai/mistral-7b-instruct |

  @requires_llm_provider
  Scenario: Fallback to other providers when OpenRouter unavailable
    Given I have configured OpenRouter as primary provider
    And OpenRouter is unavailable
    When I call generate() with prompt "Hello"
    Then the system should fallback to the next available provider
    And I should receive a response from the fallback provider
    And fallback metrics should be recorded

  @requires_llm_provider
  Scenario: Configuration validation for OpenRouter
    Given I have invalid OpenRouter configuration
    When I attempt to initialize the provider
    Then I should receive LLMConfigurationError
    And the error message should specify the configuration issue
    And the error should suggest how to fix the configuration

  @requires_llm_provider
  Scenario: Token tracking integration with OpenRouter
    Given I have configured OpenRouter with token tracking enabled
    When I call generate() with a long prompt
    Then token usage should be tracked correctly
    And token metrics should be recorded
    And context pruning should work when limits are approached

  @requires_llm_provider
  Scenario: Rate limiting handling with OpenRouter
    Given I have configured OpenRouter with rate limiting
    When I exceed rate limits
    Then I should receive appropriate rate limit errors
    And the system should handle rate limits gracefully
    And rate limit metrics should be recorded

  @requires_llm_provider
  Scenario: Model parameter validation
    Given I have configured OpenRouter with valid model
    When I call generate() with invalid parameters
    Then I should receive LLMConfigurationError for invalid parameters
    And the error should specify which parameters are invalid
    And the error should suggest valid parameter ranges

  @requires_llm_provider
  Scenario: Cross-provider model comparison
    Given I have configured multiple providers with similar capabilities
    When I call generate() with the same prompt on each provider
    Then I should receive comparable responses
    And response quality should be consistent across providers
    And performance characteristics should be documented

  @requires_llm_provider
  Scenario: OpenRouter provider metrics collection
    Given I have configured OpenRouter provider
    When I perform various operations
    Then request metrics should be collected
    And error metrics should be collected
    And performance metrics should be collected
    And token usage metrics should be collected
