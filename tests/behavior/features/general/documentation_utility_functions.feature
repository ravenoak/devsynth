Feature: Documentation Utility Functions
  As a developer
  I want to use specialized utility functions for common documentation queries
  So that I can efficiently find the information I need

  Background:
    Given the documentation management system is initialized
    And documentation for multiple libraries is available:
      | library | version |
      | numpy   | 1.22.4  |
      | pandas  | 1.4.2   |
      | scipy   | 1.8.1   |
      | sklearn | 1.1.2   |

  Scenario: Query for function documentation
    When I use the function documentation utility with "pandas.DataFrame.groupby"
    Then I should receive documentation specifically for that function
    And the results should include parameter descriptions
    And the results should include return value information
    And the results should include example usage

  Scenario: Query for class documentation
    When I use the class documentation utility with "sklearn.ensemble.RandomForestClassifier"
    Then I should receive documentation specifically for that class
    And the results should include constructor parameters
    And the results should include method listings
    And the results should include inheritance information

  Scenario: Query for usage examples
    When I use the examples utility with "numpy.array"
    Then I should receive only example code snippets
    And the results should be ranked by relevance
    And each example should include explanatory comments

  Scenario: Query for API compatibility
    When I use the compatibility utility with "pandas.read_csv" across versions:
      | version |
      | 1.3.0   |
      | 1.4.0   |
      | 1.4.2   |
    Then I should receive compatibility information
    And the results should highlight parameter changes between versions
    And the results should note deprecated features

  Scenario: Query for related functions
    When I use the related functions utility with "scipy.stats.ttest_ind"
    Then I should receive a list of related statistical functions
    And the results should include brief descriptions of each function
    And the results should explain the relationships between functions

  Scenario: Query for common usage patterns
    When I use the usage patterns utility with "sklearn.model_selection.train_test_split"
    Then I should receive common usage patterns
    And the results should include best practices
    And the results should include common parameter combinations
