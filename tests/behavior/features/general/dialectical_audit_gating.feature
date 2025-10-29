Feature: Dialectical Audit Gating
  As a release maintainer
  I want release verification to fail when dialectical audit has unresolved questions
  So that specification-implementation gaps block releases

  @fast @reqid-dialectical-audit-gating
  Scenario: Production releases require zero unresolved questions
    Given the dialectical audit identifies unresolved questions
    And the release type is production
    When I execute release verification
    Then the verification fails with unresolved questions
    And deployment is blocked until questions are resolved

  @fast @reqid-dialectical-audit-gating
  Scenario: Alpha releases allow limited unresolved questions
    Given the dialectical audit identifies some unresolved questions
    And the release type is alpha
    And unresolved questions are below the alpha threshold
    When I execute release verification
    Then the verification succeeds with warnings
    And deployment proceeds with documented risk acceptance

  @fast @reqid-dialectical-audit-gating
  Scenario: Audit execution completes within performance bounds
    Given a codebase with specifications, tests, and implementation
    When the dialectical audit executes
    Then audit completion takes less than 30 seconds
    And results are deterministic and reproducible
    And diagnostic information is provided for failures
