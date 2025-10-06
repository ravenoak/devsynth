Feature: Metrics Module
  As a project maintainer
  I want to record alignment and test metrics
  So that reports are accurate

  Scenario: Record alignment metric
    Given the metrics module
    When I record an alignment metric
    Then the metric is stored for reporting
