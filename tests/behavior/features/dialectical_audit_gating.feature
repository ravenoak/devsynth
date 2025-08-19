Feature: Dialectical audit gating
  As a release engineer
  I want the release verification to fail when unresolved audit questions exist
  So that releases only proceed with consensus

  Scenario: Release verification fails with unresolved questions
    Given dialectical_audit.log contains an unresolved question
    When verifying the release state
    Then the verification fails
