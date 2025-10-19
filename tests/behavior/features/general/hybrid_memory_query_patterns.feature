Feature: Hybrid Memory Query Patterns and Synchronization
  As a developer using DevSynth
  I want to use advanced query patterns across multiple memory stores
  So that I can efficiently retrieve and maintain consistent information across the hybrid memory system

  Background:
    Given the DevSynth system is initialized
    And the Memory Manager is configured with the following adapters:
      | adapter_type | enabled |
      | Graph        | true    |
      | Vector       | true    |
      | TinyDB       | true    |
      | Document     | true    |

  Scenario: Direct Store Query
    Given I have stored information across multiple memory stores
    When I perform a direct query to the Vector store for "code implementation examples"
    Then I should receive results only from the Vector store
    And the results should be ranked by semantic similarity
    When I perform a direct query to the Graph store for relationships of "requirement-1"
    Then I should receive results only from the Graph store
    And the results should include all connected entities

  Scenario: Cross-Store Query
    Given I have stored related information across multiple memory stores
    When I perform a cross-store query for "authentication implementation"
    Then I should receive aggregated results from all relevant stores
    And the results should be grouped by store type
    And the results should include metadata about their source store

  Scenario: Cascading Query
    Given I have stored interconnected information across multiple memory stores
    When I perform a cascading query starting with "user-story-5" in the Document store
    Then the query should first retrieve the document from the Document store
    And then follow references to retrieve related requirements from the TinyDB store
    And then follow references to retrieve related code implementations from the Vector store
    And then follow references to retrieve relationship data from the Graph store
    And the results should maintain the traversal path information

  Scenario: Federated Query
    Given I have stored distributed information across multiple memory stores
    When I perform a federated query for "error handling patterns"
    Then the query should be distributed to all memory stores in parallel
    And results should be collected from all stores
    And results should be merged and deduplicated
    And results should be ranked by relevance across all stores

  Scenario: Context-Aware Query
    Given I have stored information across multiple memory stores
    And I have an active context with the following values:
      | key           | value                 |
      | current_task  | implement_auth_system |
      | language      | python                |
      | priority      | high                  |
    When I perform a context-aware query for "best practices"
    Then the query should be enhanced with context information
    And results should be filtered based on relevance to the current context
    And results should be ranked by applicability to the current task

  Scenario: Synchronization between stores
    Given I have configured synchronization between the Vector store and the Graph store
    When I update an item in the Vector store
    Then the corresponding item in the Graph store should be automatically updated
    And the synchronization should maintain referential integrity
    And the synchronization should log the operation for audit purposes

  Scenario: Conflict resolution during synchronization
    Given I have configured synchronization between multiple stores
    When I update the same logical item in two different stores
    Then the system should detect the conflict
    And apply the configured conflict resolution strategy
    And maintain a record of the conflict and resolution
    And ensure the final state is consistent across all stores

  Scenario: Transaction boundaries across stores
    Given I have configured transaction support across stores
    When I perform a multi-store operation that updates items in Vector, Graph, and TinyDB stores
    Then all updates should be applied atomically
    And if any store update fails, all updates should be rolled back
    And the transaction should be logged with its success or failure status

  Scenario: Asynchronous synchronization with eventual consistency
    Given I have configured asynchronous synchronization between stores
    When I update an item in the primary store
    Then the update should be queued for propagation to secondary stores
    And secondary stores should eventually reflect the update
    And the system should track synchronization status
    And queries should indicate if results might include stale data
