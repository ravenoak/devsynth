Feature: CLI Entrypoint
  As a user
  I want to analyze a repository or run the CLI
  So that I can interact with DevSynth from the command line

  Scenario: Analyze repository via entrypoint
    Given a sample repository path
    When I run "devsynth --analyze-repo PATH"
    Then it outputs JSON analysis
