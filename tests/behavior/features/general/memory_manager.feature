Feature: Memory Manager and Adapters
  As a developer using DevSynth
  I want to use the Memory Manager with specialized adapters
  So that I can efficiently query different types of memory and tag items with EDRR phases

  Background:
    Given the DevSynth system is initialized
    And the Memory Manager is configured with the following adapters:
      | adapter_type | enabled |
      | Graph        | true    |
      | Vector       | true    |
      | TinyDB       | true    |

  Scenario: Query memory using GraphMemoryAdapter
    Given I have stored the following memory items with relationships:
      | id  | content       | type       | related_to |
      | id1 | Code snippet 1 | CODE      | id2        |
      | id2 | Code snippet 2 | CODE      | id3        |
      | id3 | Requirement 1  | REQUIREMENT | id1        |
    When I query the graph for items related to "id1"
    Then I should receive a list of related memory items
    And the list should contain items with ids "id2" and "id3"

  Scenario: Query memory using VectorMemoryAdapter
    Given I have stored the following memory items with embeddings:
      | content       | type       | embedding                    |
      | Code snippet 1 | CODE      | [0.1, 0.2, 0.3, 0.4, 0.5]    |
      | Code snippet 2 | CODE      | [0.2, 0.3, 0.4, 0.5, 0.6]    |
      | Requirement 1  | REQUIREMENT | [0.5, 0.6, 0.7, 0.8, 0.9]    |
    When I perform a similarity search with embedding [0.1, 0.2, 0.3, 0.4, 0.5]
    Then I should receive a list of similar memory items
    And the first item should have content "Code snippet 1"
    And the second item should have content "Code snippet 2"

  Scenario: Query memory using TinyDBMemoryAdapter
    Given I have stored the following memory items with structured data:
      | content       | type       | metadata                                |
      | Code snippet 1 | CODE      | {"language": "python", "tags": ["util"]} |
      | Code snippet 2 | CODE      | {"language": "javascript", "tags": ["ui"]} |
      | Requirement 1  | REQUIREMENT | {"priority": "high", "status": "active"} |
    When I query TinyDB with condition "language == python"
    Then I should receive a list of matching memory items
    And the list should contain 1 item
    And the first item should have content "Code snippet 1"

  Scenario: Tag memory items with EDRR phases
    When I store a memory item with content "Test content", type "CODE", and EDRR phase "EXPAND"
    Then I should receive a memory item ID
    And I should be able to retrieve the memory item using its ID
    And the retrieved memory item should have metadata with "edrr_phase" set to "EXPAND"

  Scenario: Query memory items by EDRR phase
    Given I have stored the following memory items with EDRR phases:
      | content       | type       | edrr_phase |
      | Code snippet 1 | CODE      | EXPAND     |
      | Code snippet 2 | CODE      | DIFFERENTIATE |
      | Requirement 1  | REQUIREMENT | REFINE     |
      | Requirement 2  | REQUIREMENT | RETROSPECT |
    When I query memory items by EDRR phase "EXPAND"
    Then I should receive a list of matching memory items
    And the list should contain 1 item
    And the first item should have content "Code snippet 1"

  Scenario: Maintain relationships between items across EDRR phases
    Given I have stored the following memory items with EDRR phases and relationships:
      | id  | content       | type       | edrr_phase    | related_to |
      | id1 | Initial idea  | IDEA       | EXPAND        |            |
      | id2 | Refined idea  | IDEA       | DIFFERENTIATE | id1        |
      | id3 | Implementation| CODE       | REFINE        | id2        |
      | id4 | Review        | REVIEW     | RETROSPECT    | id3        |
    When I query the graph for the evolution of item "id1" across EDRR phases
    Then I should receive a list of related memory items in EDRR phase order
    And the list should contain items with ids "id1", "id2", "id3", and "id4"
    And the items should be ordered by EDRR phase: "EXPAND", "DIFFERENTIATE", "REFINE", "RETROSPECT"
