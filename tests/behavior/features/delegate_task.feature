Feature: Multi-agent task delegation
  As a coordinator
  I want to delegate tasks to a team of agents
  So that they collaborate to produce a consensus result

  Scenario: Delegate a team task to multiple agents
    Given a team coordinator with multiple agents
    When I delegate a collaborative team task
    Then each agent should process the task
    And the delegation result should include all contributors
    And the delegation method should be consensus based
