Feature: Performance and scalability testing
  As a DevSynth maintainer
  I want to benchmark core operations
  So that the system's scalability characteristics are understood

  Background:
    Given the project environment is prepared
    And performance results are cleared

  @slow
  Scenario: baseline metrics are captured
    Given a workload of 100000 operations
    When the baseline performance task runs
    Then a metrics file "docs/performance/baseline_metrics.json" is created

  @slow
  Scenario: baseline throughput is calculated
    Given a workload of 100000 operations
    When the baseline performance task runs
    Then the metrics file "docs/performance/baseline_metrics.json" includes throughput

  @slow
  Scenario Outline: scalability metrics are captured for varying workloads
    Given a workload of <workload> operations
    When the scalability performance task runs
    Then the results include an entry for <workload>

    Examples:
      | workload |
      | 10000    |
      | 100000   |
      | 1000000  |
