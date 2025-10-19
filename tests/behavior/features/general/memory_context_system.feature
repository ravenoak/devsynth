Feature: Memory and Context System
  As a developer using DevSynth
  I want to use the Memory and Context System
  So that I can store, retrieve, and search for information during the development process

  Background:
    Given the DevSynth system is initialized
    And a memory store is configured
    And a context manager is configured

  Scenario: Store and retrieve memory item
    When I store a memory item with content "Test content" and type "CODE"
    Then I should receive a memory item ID
    And I should be able to retrieve the memory item using its ID
    And the retrieved memory item should have content "Test content" and type "CODE"

  Scenario: Store memory item with metadata
    When I store a memory item with content "Test content", type "CODE", and metadata:
      | key        | value           |
      | file_path  | /path/to/file.py |
      | language   | python          |
      | created_by | test_user       |
    Then I should receive a memory item ID
    And I should be able to retrieve the memory item using its ID
    And the retrieved memory item should have the specified metadata

  Scenario: Search for memory items
    Given I have stored the following memory items:
      | content       | type       | metadata                                |
      | Code snippet 1 | CODE      | {"language": "python", "tags": ["util"]} |
      | Code snippet 2 | CODE      | {"language": "javascript", "tags": ["ui"]} |
      | Requirement 1  | REQUIREMENT | {"priority": "high", "status": "active"} |
    When I search for memory items with query:
      | key      | value    |
      | type     | CODE     |
      | language | python   |
    Then I should receive a list of matching memory items
    And the list should contain 1 item
    And the first item should have content "Code snippet 1"

  Scenario: Add and retrieve context values
    When I add a value "test value" to the context with key "test_key"
    Then I should be able to retrieve the value using the key "test_key"
    And the retrieved value should be "test value"

  Scenario: Get full context
    Given I have added the following values to the context:
      | key       | value           |
      | user      | test_user       |
      | project   | test_project    |
      | language  | python          |
    When I request the full context
    Then I should receive a dictionary with all context values
    And the dictionary should contain the keys "user", "project", and "language"
    And the values should match what was added

  Scenario: Context persistence across operations
    Given I have added a value "test value" to the context with key "test_key"
    When I perform multiple memory operations
    Then I should still be able to retrieve the value using the key "test_key"
    And the retrieved value should be "test value"
