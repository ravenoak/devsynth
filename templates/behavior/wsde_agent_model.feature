Feature: WSDE Agent Model Refinement
  As a developer using DevSynth
  I want to use the refined WSDE agent model
  So that I can benefit from non-hierarchical, context-driven agent collaboration

  Background:
    Given the DevSynth system is initialized
    And a team of agents is configured
    And the WSDE model is enabled

  Scenario: Peer-based collaboration
    When I create a team with multiple agents
    Then all agents should be treated as peers
    And no agent should have permanent hierarchical authority
    And agents should be able to collaborate without rigid role sequences

  Scenario: Context-driven leadership
    Given a team with multiple agents with different expertise
    When a task requiring specific expertise is assigned
    Then the agent with the most relevant expertise should become the temporary Primus
    And the Primus role should change based on the task context
    And the previous Primus should return to peer status

  Scenario: Autonomous collaboration
    Given a team with multiple agents
    When a complex task is assigned
    Then any agent should be able to propose solutions at any stage
    And any agent should be able to provide critiques at any stage
    And the system should consider input from all agents

  Scenario: Consensus-based decision making
    Given a team with multiple agents
    When multiple solutions are proposed for a task
    Then the system should facilitate consensus building
    And the final decision should reflect input from all relevant agents
    And no single agent should have dictatorial authority

  Scenario: Dialectical review process
    Given a team with a Critic agent
    When a solution is proposed
    Then the Critic agent should apply dialectical reasoning
    And the Critic should identify thesis and antithesis
    And the team should work toward a synthesis
    And the final solution should reflect the dialectical process
