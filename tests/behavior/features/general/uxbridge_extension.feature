# Related issue: ../../docs/specifications/uxbridge_extension.md
Feature: Uxbridge extension
  As a developer
  I want to ensure the Uxbridge extension specification has BDD coverage
  So that the system behavior aligns with requirements

  @fast @reqid-uxbridge-extension
  Scenario: Validate Uxbridge extension
    Given the specification "uxbridge_extension.md" exists
    Then the BDD coverage acknowledges the specification
