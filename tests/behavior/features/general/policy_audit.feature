# Related issue: ../../../../docs/specifications/policy_audit.md
Feature: Policy audit
  As a developer
  I want to detect policy violations in configs and code
  So that insecure settings are caught early

  Scenario: Detect hardcoded password
    Given a config file "unsafe.cfg" containing "password=123"
    When I run the policy audit on that file
    Then the audit should report a violation
