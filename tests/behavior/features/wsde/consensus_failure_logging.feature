# Related issue: ../../../../docs/specifications/consensus_failure_logging.md
Feature: Consensus failure logging
  Scenario: Consensus vote failure triggers logging and fallback
    Given a WSDE team whose vote fails to reach a decision
    When the team runs consensus on a task
    Then a consensus failure is logged
    And the result includes a fallback consensus
