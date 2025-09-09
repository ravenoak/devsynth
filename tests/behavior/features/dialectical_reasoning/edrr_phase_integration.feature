Feature: Reasoning loop integrates with EDRR phases
  As a methodology developer
  I want reasoning results persisted with phase context
  So that EDRR history remains accessible

  @fast
  Scenario: Reasoning persistence via memory manager
    Given a dialectical reasoner with memory
    And a requirement change
    When the change is evaluated
    Then the reasoning result should be stored in memory with phase "EXPAND"

  @fast
  Scenario: Consensus failure is recorded
    Given a dialectical reasoner with memory
    And a requirement change
    When the change is evaluated with invalid consensus output
    Then the reasoning result should be stored in memory with phase "RETROSPECT"
    And a consensus error is raised
