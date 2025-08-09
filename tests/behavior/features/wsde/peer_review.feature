Feature: WSDE Peer Review Workflow
  As a developer using DevSynth
  I want work products reviewed by a team and summarized
  So that I can understand consensus outcomes quickly

  Scenario: Consensus summary after peer review
    Given the DevSynth system is initialized
    And a team of agents is configured
    And the WSDE model is enabled
    And a simple work product and two reviewers
    When the peer review workflow is executed
    Then a consensus result should be produced
    And the system should provide a summary of the consensus

  Scenario: Summarize voting results
    Given a voting result with a clear winner
    When the team summarizes the voting result
    Then the summary should mention the winning option
