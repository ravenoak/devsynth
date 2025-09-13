# Related issue: ../../../../docs/specifications/security_audit_reporting.md
Feature: Security audit reporting
  As a developer
  I want the security audit command to produce a summary report
  So that I can verify compliance results

  Scenario: Generate audit report
    Given the security audit pre-deployment checks are approved
    When I run the command "devsynth security-audit --report audit.json"
    Then the audit report "audit.json" should contain "bandit" and "safety" results
    And the workflow should execute successfully
