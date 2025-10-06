Feature: Promise System Capability Management
  As a developer using DevSynth
  I want to manage agent promises through the broker
  So that capabilities are enforced and auditable

  Background:
    Given the Promise System is initialized
    And an agent "code_agent" is registered with the system
    And an agent "analysis_agent" is registered with the system

  Scenario: Agent registers a capability
    When agent "code_agent" registers capability "CODE_GENERATION" with constraints:
      | constraint        | value                       |
      | max_file_size     | 1000000                     |
      | allowed_languages | python,javascript,typescript |
      | forbidden_paths   | /etc,/usr                   |
    Then agent "code_agent" should have capability "CODE_GENERATION"
    And the capability should have the specified constraints

  Scenario: Agent creates and fulfills a promise
    Given agent "code_agent" has capability "CODE_GENERATION"
    When agent "code_agent" creates a promise of type "CODE_GENERATION" with parameters:
      | parameter   | value                           |
      | file_path   | /project/src/module.py          |
      | language    | python                          |
      | description | Implement data processing function |
    And agent "code_agent" fulfills the promise with result:
      | key       | value                                |
      | file_path | /project/src/module.py              |
      | code      | def process_data(input_data):\n    pass |
      | success   | true                                |
    Then a new promise should be created
    And the promise should be in "FULFILLED" state
    And the promise should have the result data

  Scenario: Unauthorized agent cannot create a promise
    Given agent "analysis_agent" does not have capability "CODE_GENERATION"
    When agent "analysis_agent" attempts to create a promise of type "CODE_GENERATION"
    Then the operation should be denied
    And no promise should be created

  Scenario: Creating a chain of promises
    Given agent "analysis_agent" has capability "CODE_ANALYSIS"
    When agent "analysis_agent" creates a parent promise of type "CODE_ANALYSIS"
    And agent "analysis_agent" creates child promises for each file to analyze
    Then a promise chain should be created
    And all promises in the chain should be linked correctly
