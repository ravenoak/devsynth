Feature: Link requirement changes to EDRR outcomes
  As a methodology developer
  I want explicit links between requirement changes and EDRR outcomes
  So that behavior tests can validate the association

  @fast
  Scenario: Relationship record is stored with mapped EDRR phase
    Given a dialectical reasoner with memory
    And a requirement change of type "ADD"
    When the change is evaluated
    Then a requirement-to-reasoning relationship should be stored in memory with phase "EXPAND"
