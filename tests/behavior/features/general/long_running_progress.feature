Feature: CLI Long-Running Progress Telemetry
  As a DevSynth operator
  I want CLI operations to expose deterministic telemetry
  So that checkpoint history and ETA calculations remain auditable

  @fast @reqid-cli-long-running-progress-telemetry
  Scenario: Progress telemetry captures operation status
    Given a long-running CLI operation is initiated
    When the operation progresses through multiple stages
    Then progress status includes operation type and completion percentage
    And current stage information is accurately reported
    And estimated completion time is calculated

  @fast @reqid-cli-long-running-progress-telemetry
  Scenario: Telemetry checkpoints are persisted for audit
    Given a long-running CLI operation with telemetry enabled
    When the operation advances through checkpoints
    Then each checkpoint is persisted to audit logs
    And checkpoint data includes timestamp and operation context
    And historical checkpoints remain accessible for debugging

  @fast @reqid-cli-long-running-progress-telemetry
  Scenario: Telemetry performance impact is minimal
    Given telemetry is enabled for CLI operations
    When operations complete with and without telemetry
    Then telemetry overhead is less than 1% of operation time
    And memory usage remains bounded during operation
    And telemetry operations complete within 100ms
