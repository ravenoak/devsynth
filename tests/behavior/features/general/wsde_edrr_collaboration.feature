# Related issue: ../../../../docs/specifications/wsde_edrr_collaboration.md
Feature: WSDE and EDRR collaboration
  The WSDE team and EDRR coordinator should share phase state
  and ensure memory consistency across transitions.

  Scenario: Role assignments are exposed and memory queues are flushed
    Given the DevSynth system is initialized
    And the WSDE team is configured with agents having different expertise
    And the EDRR coordinator is initialized with enhanced features
    When I start an EDRR cycle with a task to "draft collaboration spec"
    And the EDRR cycle progresses to the "REFINE" phase
    Then the current role assignments should be accessible
    And the memory queue should be flushed
