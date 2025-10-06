# Specification: docs/specifications/integrate-dialectical-audit-into-ci.md
Feature: Integrate dialectical audit into CI
  As a maintainer
  I want CI to check for unresolved dialectical questions
  So that mismatched documentation, tests, and code are caught early

  Scenario: CI fails when the audit raises questions
    Given the repository has unresolved dialectical audit questions
    When the CI workflow runs the dialectical audit
    Then the workflow should fail

  Scenario: CI passes when the audit finds no questions
    Given the dialectical audit log contains no questions
    When the CI workflow runs the dialectical audit
    Then the workflow should succeed
