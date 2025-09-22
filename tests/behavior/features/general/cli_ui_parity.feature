Feature: CLI UI Parity
  As a developer
  I want the CLI to match the Web UI
  So that I can switch between interfaces seamlessly

  Scenario: Streamlined wizard matches web UI steps
    Given the CLI wizard is initialized
    When I compare the CLI wizard steps with the web UI
    Then the number of steps should be the same
    And the order of steps should match

  Scenario: CLI progress indicator mirrors web UI
    Given the CLI is initialized
    When I run a long-running CLI operation
    Then the CLI progress indicator should mirror the web UI progress behavior

  Scenario: Shell completion suggestions match web UI options
    Given the CLI shell completion is initialized
    When I request completions for a partial command
    Then I should receive the same suggestions as the web UI

  Scenario: CLI prompt defaults mirror web UI selection
    Given a CLI question with a default answer
    When both interfaces prompt for the same question
    Then the default responses should match
