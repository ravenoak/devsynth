# Related issue: ../../../../docs/specifications/security_audit_reporting.md
Feature: Security audit reporting
  As a developer
  I want the security audit command to produce a summary report
  So that I can verify compliance results

  Background:
    Given the DevSynth system is initialized
    And the security audit system is configured
    And I have a project with security requirements

  @medium @security
  Scenario: Generate audit report
    Given the security audit pre-deployment checks are approved
    When I run the command "devsynth security-audit --report audit.json"
    Then the audit report "audit.json" should contain "bandit" and "safety" results
    And the workflow should execute successfully

  @fast @security
  Scenario: Comprehensive security validation
    Given comprehensive security validation is enabled
    When I run comprehensive security audit
    Then the system should run Bandit static analysis
    And the system should scan dependencies for vulnerabilities
    And the system should validate security policies
    And the system should generate a comprehensive security report

  @fast @security
  Scenario: Vulnerability management
    Given I have vulnerabilities in my project
    When I scan for security vulnerabilities
    Then the system should identify all vulnerabilities
    And the system should prioritize vulnerabilities by risk
    And the system should generate a remediation plan
    And the system should track vulnerability resolution

  @fast @security
  Scenario: Security compliance validation
    Given I have security compliance requirements
    When I validate security compliance
    Then the system should check OWASP compliance
    And the system should validate access controls
    And the system should audit encryption usage
    And the system should generate compliance report

  @medium @security
  Scenario: Security enhancement integration
    Given I have security gaps in my code
    When I run security enhancement
    Then the system should identify security improvements
    And the system should apply safe security fixes
    And the system should validate fixes don't break functionality
    And the system should report security improvements

  @fast @security
  Scenario: Security monitoring integration
    Given security monitoring is enabled
    When code changes are made
    Then the system should detect security impacts
    And the system should generate security alerts
    And the system should suggest security improvements
    And the system should track security trends
