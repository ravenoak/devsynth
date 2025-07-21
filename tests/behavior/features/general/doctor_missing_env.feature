Feature: Doctor command with missing environment variables
  As a developer
  I want warnings when essential environment variables are absent
  So that I can configure them correctly

  Scenario: Warn when OPENAI_API_KEY is missing
    Given essential environment variables are missing
    When I run the command "devsynth doctor"
    Then the output should mention the missing variables
