Feature: Dialectical audit gating
  As a release maintainer
  I want release verification to fail when dialectical audit log has unresolved questions
  So that unresolved issues block releases

  Scenario: Release verification fails when unresolved questions remain
    Given the dialectical audit log contains unresolved questions
    When I verify the release state
    Then the release verification should fail
