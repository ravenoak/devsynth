# Specification: docs/specifications/multi-agent-collaboration.md
@fast
Feature: Multi-Agent Collaboration
  As a development coordinator
  I want agents to agree on a proposal through majority consensus
  So that the system follows a unified decision

  Scenario: Majority vote selects a proposal
    Given a coordinator managing three agents
    And the agents propose "refactor", "refactor", and "document"
    When the coordinator collects their votes
    Then the final decision is "refactor"
    And the round completes successfully
