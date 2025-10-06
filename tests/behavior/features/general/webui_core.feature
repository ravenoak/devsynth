# Related issue: ../../docs/specifications/webui-core.md
Feature: Webui core
  As a developer
  I want to ensure the Webui core specification has BDD coverage
  So that the system behavior aligns with requirements

  @fast @reqid-webui-core
  Scenario: Validate Webui core
    Given the specification "webui-core.md" exists
    Then the BDD coverage acknowledges the specification
