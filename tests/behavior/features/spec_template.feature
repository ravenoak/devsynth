# Related issue: ../../docs/specifications/spec_template.md
Feature: Spec template
  As a developer
  I want to ensure the Spec template specification has BDD coverage
  So that the system behavior aligns with requirements

  @fast @reqid-spec-template
  Scenario: Validate Spec template
    Given the specification "spec_template.md" exists
    Then the BDD coverage acknowledges the specification
