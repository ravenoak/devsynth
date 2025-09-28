Feature: CLI long-running progress telemetry
  As a DevSynth operator
  I want CLI runs to expose deterministic telemetry
  So that checkpoint history and ETA calculations stay auditable

  Scenario: Telemetry is recorded for CLI tasks
    Given the long-running progress indicator is active for "etl"
    When the task advances through multiple statuses
    Then history entries and checkpoints are persisted for audit logs
