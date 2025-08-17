Feature: Sprint ceremonies align with EDRR phases
  The SprintAdapter maps common Agile ceremonies to the corresponding EDRR
  phases so teams can track progress through Expand, Differentiate, Refine,
  and Retrospect.

  Scenario: Mapping ceremonies to phases
    Given a sprint adapter
    Then the "planning" ceremony maps to "expand"
    And the "dailyStandup" ceremony maps to "differentiate"
    And the "review" ceremony maps to "refine"
    And the "retrospective" ceremony maps to "retrospect"
