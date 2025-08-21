# Specification: docs/specifications/multi-agent-collaboration.md
Feature: Multi-Agent Collaboration
  As a developer
  I want agents to coordinate through a consensus mechanism
  So that the system adopts a single shared decision

  Scenario: Coordinating conflicting proposals
    Given a coordinator with three voting agents
    When two agents propose "A" and one proposes "B"
    Then the coordinator chooses "A" as the consensus decision
