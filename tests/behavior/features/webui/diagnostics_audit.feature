Feature: Diagnostics displays audit logs
  As a developer
  I want to view dialectical audit logs in the WebUI diagnostics page
  So that I can diagnose issues using audit information

  Background:
    Given the WebUI is initialized

  Scenario: View dialectical audit log
    Given an audit log is present
    When I navigate to "Diagnostics"
    Then the dialectical audit log should be displayed

  Scenario: Audit log missing
    Given no audit log is present
    When I navigate to "Diagnostics"
    Then a message indicates no audit logs are available
