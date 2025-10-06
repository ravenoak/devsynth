Feature: Memory adapter read and write operations
  Scenario: Store and retrieve a memory item
    Given a memory system adapter
    When I write "test content" to memory
    And I read the item from memory
    Then the retrieved content should be "test content"
