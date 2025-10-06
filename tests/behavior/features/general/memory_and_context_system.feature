Feature: Memory and Context System
  As a DevSynth maintainer
  I want the memory system to categorise items and expose session context
  So that iterative workflows retain the right information between phases

  Background:
    Given a multi-layered memory system
    And a simple context manager

  Scenario: classify stored items by type and surface context values
    When I store a memory item with content "Current task outline" and type "CONTEXT"
    And I store a memory item with content "Sprint retrospective" and type "TASK_HISTORY"
    And I store a memory item with content "Prompt templates" and type "KNOWLEDGE"
    And I add the context value "last_phase" as "REFINE"
    And I add the context value "active_goal" as "Improve coverage"
    When I request the full context
    Then the short-term layer should contain "Current task outline"
    And the episodic layer should contain "Sprint retrospective"
    And the semantic layer should contain "Prompt templates"
    And the full context should include key "last_phase" with value "REFINE"
    And the full context should include key "active_goal" with value "Improve coverage"

  Scenario: retrieving an existing item returns the latest content
    When I store a memory item with id "ctx-1", content "First draft", and type "CONTEXT"
    And I store a memory item with id "ctx-1", content "Final draft", and type "CONTEXT"
    Then retrieving "ctx-1" should return content "Final draft"
