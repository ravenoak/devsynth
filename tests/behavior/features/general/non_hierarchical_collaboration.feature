Feature: Non-Hierarchical Collaboration
  As a developer
  I want to use non-hierarchical collaboration in WSDE teams
  So that agents can work together more effectively without rigid hierarchies

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

  Scenario: Adaptive leadership selection
    Given a task with changing requirements
    When the requirements change during task execution
    Then the team should reassess leadership roles
    And the primus role should be reassigned if necessary
    And the transition should be smooth without disrupting progress
    And the new leadership should better address the changed requirements

  Scenario: Collaborative problem-solving without hierarchy
    Given a problem with no clear solution approach
    When the team collaborates to solve the problem
    Then all agents should propose potential approaches
    And the team should evaluate approaches based on merit not agent status
    And the selected approach should be refined collaboratively
    And the implementation should involve multiple agents working as peers
