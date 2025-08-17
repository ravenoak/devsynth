Feature: Deployment environment validation
  As a developer
  I want the deployment script to verify prerequisites
  So that misconfigured environments are detected early

  Scenario: Docker missing in containerized environment
    Given Docker is not installed
    When the deployment script is executed
    Then an error is reported about Docker being required
