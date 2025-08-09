# Integration Tests

This directory contains integration tests for the DevSynth project. These tests verify that different components of the system work together correctly.

## Running Integration Tests

To run all integration tests:

```bash
python -m pytest tests/integration
```

To run a specific test:

```bash
python -m pytest tests/integration/test_file_name.py
```

## Test Categories

### EDRR Integration Tests

#### Mock LLM Integration

The `test_edrr_mock_llm_integration.py` file contains tests that use a mock LLM provider to test the EDRR cycle. These tests don't require any API keys or external services.

#### Real LLM Integration

The `test_edrr_real_llm_integration.py` file contains tests that use real LLM providers to test the EDRR cycle. These tests require valid API keys or endpoints to be configured in environment variables.

The file contains two test cases:

1. `test_edrr_cycle_with_real_llm`: A simple test that asks the EDRR framework to create a function to calculate the factorial of a number.
2. `test_edrr_cycle_with_real_project`: A more complex test that creates a small Flask application with issues and asks the EDRR framework to analyze and improve it by adding proper data validation, error handling, and following best practices.

To run the real LLM integration tests, you need to set one of the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `LM_STUDIO_ENDPOINT`: The endpoint for your LM Studio instance (default: http://127.0.0.1:1234)

Example:

```bash
# Using OpenAI
export OPENAI_API_KEY=your_api_key
python -m pytest tests/integration/test_edrr_real_llm_integration.py

# Using LM Studio
export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
python -m pytest tests/integration/test_edrr_real_llm_integration.py

# Run a specific test case
python -m pytest tests/integration/test_edrr_real_llm_integration.py::test_edrr_cycle_with_real_llm
python -m pytest tests/integration/test_edrr_real_llm_integration.py::test_edrr_cycle_with_real_project
```

If neither environment variable is set, the tests will be skipped.

### Memory System Integration Tests

The `test_graph_memory_edrr_integration.py` file contains tests that verify the integration between the graph memory system and the EDRR framework.

### End-to-End Workflow Tests

The `test_end_to_end_workflow.py` file contains tests that simulate a complete development workflow from requirements to code.

## Adding New Integration Tests

When adding new integration tests:

1. Create a new file with a name starting with `test_` in the `tests/integration` directory
2. Import the necessary components from the DevSynth project
3. Write test functions that verify the integration between different components
4. Use pytest fixtures to set up and tear down test resources
5. Document any special requirements or setup needed to run the tests
6. Start from `templates/integration/test_integration_template.py` and replace
   all placeholders with concrete assertions before committing.
