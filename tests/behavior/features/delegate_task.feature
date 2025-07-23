Feature: Multi-agent task delegation
  As a coordinator
  I want to delegate tasks to a team of agents
  So that they collaborate to produce a consensus result

  Scenario: Delegate a team task to multiple agents
    Given a team coordinator with multiple agents
    When I delegate a collaborative team task
    Then each agent should process the task
    And the consensus result should be final
    And the delegation result should include all contributors
    And the delegation method should be consensus based

  Scenario: Delegate a task with dialectical reasoning and consensus
    Given a team coordinator with multiple agents
    And a critic agent with dialectical reasoning expertise
    When I delegate a dialectical reasoning task
    Then each agent should process the task
    And the team should apply dialectical reasoning before consensus
    And the consensus result should be final
    And the delegation method should be consensus based
