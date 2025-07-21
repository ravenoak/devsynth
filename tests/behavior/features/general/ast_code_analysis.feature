Feature: AST-Based Code Analysis and Transformation
  As a developer using DevSynth
  I want to use AST-based code analysis and transformation
  So that I can perform precise code manipulations and gain deeper insights into code structure

  Background:
    Given the DevSynth system is initialized
    And the AST-based code analysis module is configured

  Scenario: Parse Python code into AST
    When I provide Python code to the analyzer
    Then it should parse the code into an AST representation
    And the AST should accurately represent the code structure
    And I should be able to access all code elements through the AST

  Scenario: Extract code structure information
    Given I have Python code with classes, functions, and variables
    When I analyze the code using the AST analyzer
    Then I should receive a structured representation of the code
    And the representation should include all classes with their methods
    And the representation should include all functions with their parameters
    And the representation should include all variables with their types

  Scenario: Perform AST-based code transformations
    Given I have Python code that needs refactoring
    When I request an AST-based transformation
    Then the system should modify the AST according to the transformation rules
    And the system should generate valid Python code from the modified AST
    And the transformed code should maintain the original functionality

  Scenario: Extract function definitions
    Given I have Python code with multiple function definitions
    When I request to extract function definitions using AST
    Then the system should identify all functions in the code
    And for each function, it should extract the signature, parameters, and return type
    And the extracted information should be stored in the memory system

  Scenario: Rename identifiers
    Given I have Python code with identifiers that need renaming
    When I request to rename an identifier using AST transformation
    Then the system should identify all occurrences of the identifier
    And it should rename all occurrences while preserving scope rules
    And the resulting code should be valid Python with the updated identifier

  Scenario: Remove unused imports
    Given I have Python code with unused imports
    When I request to remove unused imports using AST transformation
    Then the system should identify all unused imports
    And it should remove all unused imports from the code
    And the resulting code should be valid Python without the unused imports

  Scenario: Remove redundant assignments
    Given I have Python code with redundant assignments
    When I request to remove redundant assignments using AST transformation
    Then the system should identify all redundant assignments
    And it should remove all redundant assignments from the code
    And the resulting code should be valid Python with the same functionality

  Scenario: Remove unused variables
    Given I have Python code with unused variables
    When I request to remove unused variables using AST transformation
    Then the system should identify all unused variables
    And it should remove all unused variables from the code
    And the resulting code should be valid Python without the unused variables

  Scenario: Optimize string literals
    Given I have Python code with string literals that can be optimized
    When I request to optimize string literals using AST transformation
    Then the system should identify string literals that can be optimized
    And it should optimize the string literals in the code
    And the resulting code should be valid Python with optimized string literals

  Scenario: Improve code style
    Given I have Python code with style issues
    When I request to improve code style using AST transformation
    Then the system should identify style issues in the code
    And it should apply style improvements to the code
    And the resulting code should follow Python style guidelines

  Scenario: Apply multiple transformations
    Given I have Python code that needs multiple transformations
    When I request to apply multiple AST transformations:
      | transformation_type     |
      | remove_unused_imports   |
      | remove_unused_variables |
      | optimize_string_literals|
      | improve_code_style      |
    Then the system should apply all transformations in the correct order
    And the resulting code should be valid Python with all transformations applied
    And the transformed code should maintain the original functionality

  Scenario: Integrate with EDRR workflow
    Given the EDRR workflow is configured
    When I initiate a coding task
    Then the system should use AST analysis in the Expand phase to explore implementation options
    And the system should use AST analysis in the Differentiate phase to evaluate code quality
    And the system should use AST transformations in the Refine phase to improve the code
    And the system should use AST analysis in the Retrospect phase to verify code quality
    And the memory system should store AST analysis results with appropriate EDRR phase tags
