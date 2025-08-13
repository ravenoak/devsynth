Feature: WSDE collaboration flow
  WSDE teams expose identifier-based role assignments and flush memory when roles progress.

  Scenario: progressing roles flushes memory
    Given a WSDE team with pending memory
    When the team progresses through the EXPAND phase
    Then the role assignments are returned by identifier
    And the memory queue is empty
