Feature: WSDE Model and Memory System Integration
  As a developer using DevSynth
  I want the WSDE model to be integrated with the memory system
  So that agents can store and retrieve their state, solutions, and reasoning results

  Background:
    Given the DevSynth system is initialized
    And a team of agents is configured
    And the WSDE model is enabled
    And the memory system is configured with a test backend

  Scenario: Store and retrieve WSDE team state
    When I create a team with multiple agents
    And I store the team state in memory
    Then I should be able to retrieve the team state from memory
    And the retrieved team state should match the original state

  Scenario: Store and retrieve solutions with EDRR phase tagging
    Given a team with multiple agents
    When a solution is proposed for a task
    And the solution is stored in memory with EDRR phase "Expand"
    Then I should be able to retrieve the solution by EDRR phase
    And the solution should have the correct EDRR phase tag

  Scenario: Store and retrieve dialectical reasoning results
    Given a team with a Critic agent
    When a solution is proposed
    And the Critic agent applies dialectical reasoning
    And the dialectical reasoning results are stored in memory
    Then I should be able to retrieve the dialectical reasoning results
    And the retrieved results should contain thesis, antithesis, and synthesis

  Scenario: Access knowledge graph for enhanced reasoning
    Given a team with multiple agents
    And a knowledge graph with domain knowledge
    When the team needs to reason about a complex task
    Then the team should be able to query the knowledge graph
    And incorporate the knowledge into their reasoning process

  Scenario: Use different memory backends for WSDE artifacts
    Given the memory system is configured with multiple backends
    When I store WSDE artifacts in different backends
    Then I should be able to retrieve the artifacts from their respective backends
    And the artifacts should maintain their relationships
