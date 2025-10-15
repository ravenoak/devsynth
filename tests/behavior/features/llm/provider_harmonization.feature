Feature: Provider Harmonization
  As a DevSynth user
  I want all LLM providers to behave consistently
  So that I can switch between providers seamlessly

  Background:
    Given I have access to multiple LLM providers
    And all providers are properly configured

  @requires_llm_provider
  Scenario Outline: Identical interface across all providers
    Given I have configured <provider> provider
    When I call generate() with prompt "Hello, how are you?"
    Then I should receive a text response
    And the response should be a string
    And no exceptions should be raised
    And the response should contain helpful content

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |
      | offline    |

  @requires_llm_provider
  Scenario Outline: Consistent context generation across providers
    Given I have configured <provider> provider
    And I have conversation context with system message "You are a helpful coding assistant"
    When I call generate_with_context() with prompt "Explain recursion in programming" and context
    Then I should receive a text response
    And the response should be a string
    And the response should reference programming concepts
    And the response should consider the system message
    And no exceptions should be raised

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent embedding generation across providers
    Given I have configured <provider> provider
    When I call get_embedding() with text "Machine learning is fascinating"
    Then I should receive an embedding vector
    And the embedding should be a list of floats
    And the embedding should have consistent dimensions across calls
    And no exceptions should be raised

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent error handling across providers for invalid credentials
    Given I have configured <provider> provider
    And I have invalid credentials for the provider
    When I call generate() with prompt "Hello"
    Then I should receive LLMAuthenticationError
    And the error message should be descriptive
    And the error should contain helpful troubleshooting information
    And the error type should be consistent across providers

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent error handling across providers for invalid models
    Given I have configured <provider> provider
    And I have configured an invalid model name
    When I call generate() with prompt "Hello"
    Then I should receive LLMModelError
    And the error message should suggest valid model alternatives
    And the error should contain helpful troubleshooting information
    And the error type should be consistent across providers

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent configuration validation across providers
    Given I have <configuration_status> configuration for <provider> provider
    When I attempt to initialize the provider
    Then I should receive <expected_error> if configuration is invalid
    And the error message should specify the configuration issue
    And the error should suggest how to fix the configuration

    Examples:
      | provider   | configuration_status | expected_error        |
      | openai     | valid               | no error             |
      | openai     | invalid             | LLMConfigurationError |
      | anthropic  | valid               | no error             |
      | anthropic  | invalid             | LLMConfigurationError |
      | lmstudio   | valid               | no error             |
      | lmstudio   | invalid             | LLMConfigurationError |
      | openrouter | valid               | no error             |
      | openrouter | invalid             | LLMConfigurationError |

  @requires_llm_provider
  Scenario Outline: Consistent streaming support across streaming providers
    Given I have configured <provider> provider that supports streaming
    When I call generate_stream() with prompt "Tell me about artificial intelligence"
    Then I should receive an async generator
    And the generator should yield text chunks progressively
    And each chunk should be a string
    And the complete response should form coherent text
    And no exceptions should be raised

    Examples:
      | provider   |
      | openai     |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent token tracking across providers
    Given I have configured <provider> provider with token tracking enabled
    When I call generate() with a prompt that uses significant tokens
    Then token usage should be tracked correctly
    And token metrics should be recorded consistently
    And the token count should be reasonable for the prompt length

    Examples:
      | provider   |
      | openai     |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent retry behavior across providers
    Given I have configured <provider> provider with intermittent failures
    When I call generate() with prompt "Hello"
    Then the request should retry on transient errors
    And the request should succeed after retries
    And retry metrics should be recorded consistently
    And retry delays should follow exponential backoff pattern

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent circuit breaker behavior across providers
    Given I have configured <provider> provider with a failing endpoint
    When I make multiple consecutive failing requests
    Then the circuit breaker should open after the failure threshold
    And subsequent requests should fail immediately with circuit breaker error
    And the circuit breaker should attempt recovery after the timeout period
    And circuit breaker state should be tracked consistently

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario: Provider fallback chain works correctly
    Given I have configured multiple providers in fallback order
    And the primary provider becomes unavailable
    When I call generate() with prompt "Hello"
    Then the system should try each provider in fallback order
    And I should eventually receive a response from an available provider
    And fallback attempts should be logged
    And fallback metrics should be recorded

  @requires_llm_provider
  Scenario Outline: Consistent performance characteristics across providers
    Given I have configured <provider> provider
    When I perform multiple generation requests
    Then response times should be within acceptable ranges
    And throughput should meet minimum requirements
    And resource usage should be reasonable
    And performance metrics should be collected consistently

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario Outline: Consistent parameter handling across providers
    Given I have configured <provider> provider
    When I call generate() with various parameter combinations
    Then all valid parameters should be accepted
    And invalid parameters should be rejected with clear error messages
    And parameter validation should be consistent across providers
    And parameter defaults should be reasonable

    Examples:
      | provider   |
      | openai     |
      | anthropic  |
      | lmstudio   |
      | openrouter |

  @requires_llm_provider
  Scenario: Cross-provider compatibility for context format
    Given I have conversation context in OpenAI chat format
    When I use the same context with multiple providers
    Then all providers should handle the context format correctly
    And responses should consider the conversation history appropriately
    And context parsing should be consistent across providers

  @requires_llm_provider
  Scenario: Provider selection and switching works seamlessly
    Given I have multiple providers configured
    When I switch between providers dynamically
    Then the active provider should change correctly
    And subsequent requests should use the new provider
    And provider switching should be logged
    And provider metrics should reflect the switch

  @requires_llm_provider
  Scenario: Provider health monitoring works consistently
    Given I have multiple providers configured
    When providers experience various health states
    Then health status should be monitored consistently
    And unhealthy providers should be handled appropriately
    And health metrics should be collected uniformly
    And health status should influence provider selection
