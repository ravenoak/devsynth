Feature: Non-Hierarchical Collaboration
  As a developer
  I want WSDE teams to collaborate without rigid hierarchies
  So that expertise drives leadership and decision-making

  Background:
    Given a WSDE team with multiple agents
    And each agent has different expertise areas
    And the team is configured for non-hierarchical collaboration

  Scenario: Peer-based behavior in WSDE team
    When the team is assigned a task requiring multiple expertise areas
    Then all agents should contribute to the solution
    And no single agent should dominate the decision-making process
    And the contributions should be weighted based on relevant expertise
    And the final solution should incorporate insights from all agents

  Scenario: Role rotation based on task context
    Given a sequence of tasks with different expertise requirements
    When the team processes these tasks in sequence
    Then the primus role should rotate among different agents
    And each rotation should be based on task-specific expertise
    And the team should maintain a history of role assignments
    And the role rotation should improve overall solution quality

  Scenario: Expertise-based task delegation
    Given a complex task with multiple subtasks
    When the team breaks down the task into subtasks
    Then each subtask should be assigned to the agent with most relevant expertise
    And the assignments should be dynamically adjusted based on progress
    And agents should collaborate on subtasks requiring multiple expertise areas
    And the final integration should be coordinated by the most qualified agent
