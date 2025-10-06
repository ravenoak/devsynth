# Related issue: ../../docs/specifications/end_to_end_deployment.md
Feature: End to end deployment
  As a developer
  I want to ensure the End to end deployment specification has BDD coverage
  So that the system behavior aligns with requirements

  @fast @reqid-end-to-end-deployment
  Scenario: Validate End to end deployment
    Given the specification "end_to_end_deployment.md" exists
    Then the BDD coverage acknowledges the specification
