Feature: Requirement Analysis
  As a maintainer reviewing requirements
  I want the CLI to parse existing files or launch interactive intake
  So that the project memory reflects current needs

  Scenario: Analyze requirements from a text file
    Given I have initialized a DevSynth project
    And I have a requirements file "requirements.txt"
    When I run the command "devsynth inspect --input requirements.txt"
    Then the system should parse the requirements
    And create a structured representation in the memory system
    And generate a requirements summary

  Scenario: Run interactive requirement gathering
    Given I have initialized a DevSynth project
    When I run the command "devsynth inspect --interactive"
    Then the system should start an interactive session
    And ask me questions about my requirements
    And create a structured representation in the memory system
    And generate a requirements summary
