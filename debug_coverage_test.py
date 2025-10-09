#!/usr/bin/env python3
"""Debug script to understand coverage measurement issues."""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, "src")

# Import and test the utils modules directly
from devsynth.utils.logging import DevSynthLogger, get_logger, setup_logging
from devsynth.utils.serialization import (
    dump_to_file,
    dumps_deterministic,
    load_from_file,
    loads,
)


@pytest.mark.fast
def test_logging_functions():
    """Test all logging functions to see if they execute."""
    print("=== Testing Logging Functions ===")

    # Test get_logger (line 55)
    logger = get_logger("test")
    print(f"get_logger result: {type(logger)}")

    # Test setup_logging (lines 60-61)
    import devsynth.utils.logging as L

    original_configure = L.configure_logging
    L.configure_logging = lambda x: print(f"configure_logging called with {x}")

    setup_logger = setup_logging("test2", "INFO")
    print(f"setup_logging result: {type(setup_logger)}")

    L.configure_logging = original_configure

    # Test DevSynthLogger with various exc_info types
    test_logger = DevSynthLogger("debug")

    # Test with BaseException (lines 31-35)
    try:
        raise ValueError("test")
    except ValueError as e:
        test_logger.error("test with exception", exc_info=e)
        print("BaseException test completed")

    # Test with True (lines 37-38)
    try:
        raise RuntimeError("test2")
    except RuntimeError:
        test_logger.error("test with True", exc_info=True)
        print("exc_info=True test completed")

    # Test with None/False (line 40)
    test_logger.info("test with None", exc_info=None)
    test_logger.info("test with False", exc_info=False)
    print("None/False test completed")

    # Test with invalid types (line 48)
    test_logger.warning("test with invalid", exc_info="invalid")
    print("Invalid exc_info test completed")


@pytest.mark.fast
def test_serialization_functions():
    """Test all serialization functions to see if they execute."""
    print("\n=== Testing Serialization Functions ===")

    # Test dumps_deterministic (lines 28-32)
    obj = {"test": "data"}
    result = dumps_deterministic(obj)
    print(
        f"dumps_deterministic result: {len(result)} chars, ends with newline: {result.endswith('\\n')}"
    )

    # Test loads (lines 41-43)
    loaded = loads(result)
    print(f"loads result: {loaded}")

    # Test with string without newline
    json_no_newline = '{"key":"value"}'
    loaded_no_newline = loads(json_no_newline)
    print(f"loads without newline: {loaded_no_newline}")

    # Test dump_to_file and load_from_file (lines 48-50, 55-56)
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name

    try:
        dump_to_file(temp_path, obj)
        print(f"dump_to_file completed")

        loaded_from_file = load_from_file(temp_path)
        print(f"load_from_file result: {loaded_from_file}")
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    test_logging_functions()
    test_serialization_functions()
    print("\n=== All functions executed successfully ===")
