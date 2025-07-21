Feature: WSDE Voting Mechanisms for Critical Decisions
  As a developer using DevSynth
  I want to use voting mechanisms for critical decisions in the WSDE model
  So that I can ensure fair and democratic decision-making in agent teams

  Background:
    Given the DevSynth system is initialized
    And a team of agents is configured
    And the WSDE model is enabled

  Scenario: Voting on critical decisions
    Given a team with multiple agents with different expertise
    When a critical decision needs to be made
    Then the system should initiate a voting process
    And each agent should cast a vote based on their expertise
    And the decision should be made based on majority vote
    And the voting results should be recorded

  Scenario: Consensus fallback for tied votes
    Given a team with an even number of agents
    When a critical decision results in a tied vote
    Then the system should fall back to consensus-building
    And the final decision should reflect input from all agents
    And the decision-making process should be documented

  Scenario: Weighted voting based on expertise
    Given a team with agents having different levels of expertise
    When a critical decision in a specific domain needs to be made
    Then agents with relevant expertise should have weighted votes
    And the final decision should favor domain experts
    And the weighting mechanism should be transparent