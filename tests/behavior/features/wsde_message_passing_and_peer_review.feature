Feature: WSDE Message Passing and Peer Review
  As a developer using DevSynth
  I want to use structured message passing and peer review in the WSDE model
  So that agents can communicate effectively and improve output quality through systematic review

  Background:
    Given the DevSynth system is initialized
    And a team of agents is configured
    And the WSDE model is enabled

  Scenario: Message passing between agents
    Given a team with multiple agents
    When agent "worker-1" sends a message to agent "supervisor-1" with type "status_update"
    Then agent "supervisor-1" should receive the message
    And the message should have the correct sender, recipient, and type
    And the message should be stored in the communication history

  Scenario: Broadcast message to multiple agents
    Given a team with multiple agents
    When agent "primus-1" sends a broadcast message to all agents with type "task_assignment"
    Then all agents should receive the message
    And each message should have the correct sender and type
    And the broadcast should be recorded as a single communication event

  Scenario: Message passing with priority levels
    Given a team with multiple agents
    When agent "worker-1" sends a message with priority "high" to agent "primus-1"
    Then agent "primus-1" should receive the message with priority "high"
    And high priority messages should be processed before lower priority messages
    And the message priority should be recorded in the communication history

  Scenario: Message passing with structured content
    Given a team with multiple agents
    When agent "worker-1" sends a message with structured content:
      | key           | value                 |
      | task_id       | task-123              |
      | status        | in_progress           |
      | completion    | 75                    |
      | blockers      | none                  |
    Then agent "supervisor-1" should receive the message with the structured content
    And the structured content should be accessible as a parsed object
    And the message should be queryable by content fields

  Scenario: Peer review request and execution
    Given a team with multiple agents
    When agent "worker-1" submits a work product for peer review
    Then the system should assign reviewers based on expertise
    And each reviewer should receive a review request message
    And each reviewer should evaluate the work product independently
    And each reviewer should submit feedback
    And the original agent should receive all feedback

  Scenario: Peer review with acceptance criteria
    Given a team with multiple agents
    When agent "worker-1" submits a work product with specific acceptance criteria
    Then the peer review request should include the acceptance criteria
    And reviewers should evaluate the work against the criteria
    And the review results should indicate pass/fail for each criterion
    And the overall review should include a final acceptance decision

  Scenario: Peer review with revision cycle
    Given a team with multiple agents
    When agent "worker-1" submits a work product that requires revisions
    And reviewers provide feedback requiring changes
    Then agent "worker-1" should receive the consolidated feedback
    And agent "worker-1" should create a revised version
    And the revised version should be submitted for another review cycle
    And the system should track the revision history
    And the final accepted version should be marked as approved

  Scenario: Peer review with dialectical analysis
    Given a team with a Critic agent
    When a work product is submitted for peer review
    Then the Critic agent should apply dialectical analysis
    And the analysis should identify strengths (thesis)
    And the analysis should identify weaknesses (antithesis)
    And the analysis should propose improvements (synthesis)
    And the dialectical analysis should be included in the review feedback

  Scenario: Message and review history tracking
    Given a team with multiple agents that have exchanged messages
    And multiple peer reviews have been conducted
    When I request the communication history for the team
    Then I should receive a chronological record of all messages
    And I should receive a record of all peer reviews
    And the history should include metadata about senders, recipients, and timestamps
    And the history should be filterable by message type, agent, and time period
