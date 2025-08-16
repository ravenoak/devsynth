Feature: Dialectical reasoning impact memory integration
  As a requirements engineer
  I want impact assessments stored in memory
  So that they can inform future decisions

  @fast
  Scenario: Impact assessment stored with phase REFINE
    Given a dialectical reasoner with memory
    And a requirement change
    When the change impact is assessed
    Then the impact assessment should be stored in memory with phase "REFINE"

  @fast
  Scenario: Memory persistence failure is logged
    Given a dialectical reasoner with failing memory
    And a requirement change
    When the change impact is assessed
    Then the impact assessment completes
    And a memory persistence warning is logged
