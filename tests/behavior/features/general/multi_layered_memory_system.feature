Feature: Multi-Layered Memory System and Tiered Cache Strategy
  As a developer using DevSynth
  I want to use the multi-layered memory system and tiered cache strategy
  So that I can benefit from efficient memory organization and faster access to frequently used items

  Background:
    Given the DevSynth system is initialized
    And the multi-layered memory system is configured

  Scenario: Multi-layered memory system categorization
    When I store information with content "Current task context" and type "CONTEXT" in the memory system
    Then it should be categorized into the short-term memory layer
    When I store information with content "Previous task execution" and type "TASK_HISTORY" in the memory system
    Then it should be categorized into the episodic memory layer
    When I store information with content "Python language reference" and type "KNOWLEDGE" in the memory system
    Then it should be categorized into the semantic memory layer

  Scenario: Short-term memory contains immediate context
    When I store information with content "Current user request" and type "CONTEXT" in the memory system
    And I store information with content "Current conversation state" and type "CONTEXT" in the memory system
    Then the short-term memory layer should contain these items
    And I should be able to retrieve all items from the short-term memory layer

  Scenario: Episodic memory contains past events
    When I store information with content "Task execution at 2023-06-01" and type "TASK_HISTORY" in the memory system
    And I store information with content "Error encountered at 2023-06-02" and type "ERROR_LOG" in the memory system
    Then the episodic memory layer should contain these items
    And I should be able to retrieve all items from the episodic memory layer

  Scenario: Semantic memory contains general knowledge
    When I store information with content "Python dictionary usage" and type "KNOWLEDGE" in the memory system
    And I store information with content "Git workflow best practices" and type "KNOWLEDGE" in the memory system
    Then the semantic memory layer should contain these items
    And I should be able to retrieve all items from the semantic memory layer

  Scenario: Cross-layer memory querying
    Given I have stored items in all memory layers
    When I query the memory system without specifying a layer
    Then I should receive results from all memory layers
    When I query the memory system specifying the "short-term" layer
    Then I should only receive results from the short-term memory layer
    When I query the memory system specifying the "episodic" layer
    Then I should only receive results from the episodic memory layer
    When I query the memory system specifying the "semantic" layer
    Then I should only receive results from the semantic memory layer

  Scenario: Tiered cache strategy with in-memory cache
    Given the tiered cache strategy is enabled
    When I access an item from the memory system for the first time
    Then it should be retrieved from the underlying storage
    When I access the same item again
    Then it should be retrieved from the in-memory cache
    And accessing the cached item should be faster than the first access

  Scenario: Cache update based on access patterns
    Given the tiered cache strategy is enabled with a limited cache size
    When I access multiple items from the memory system
    And the cache reaches its capacity
    And I access a new item
    Then the least recently used item should be removed from the cache
    And the new item should be added to the cache
