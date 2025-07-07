import pytest
from devsynth.security.sanitization import sanitize_input, validate_safe_input
from devsynth.exceptions import InputSanitizationError


def test_sanitize_input_removes_script():
    """Test that sanitize_input removes script tags."""
    text = "<script>alert('x')</script>Hello"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello"


def test_sanitize_input_removes_control_chars():
    """Test that sanitize_input removes control characters."""
    text = "Hello\x00World\x1fTest\x7f"
    sanitized = sanitize_input(text)
    assert sanitized == "HelloWorldTest"


def test_sanitize_input_removes_both():
    """Test that sanitize_input removes both script tags and control characters."""
    text = "<script>alert('x')\x00</script>Hello\x1fWorld"
    sanitized = sanitize_input(text)
    assert sanitized == "HelloWorld"


def test_sanitize_input_strips_whitespace():
    """Test that sanitize_input strips whitespace."""
    text = "  Hello World  "
    sanitized = sanitize_input(text)
    assert sanitized == "Hello World"


def test_sanitize_input_no_script_tags():
    """Test that sanitize_input works correctly when there are no script tags to remove."""
    text = "Hello World"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello World"


def test_sanitize_input_no_control_chars():
    """Test that sanitize_input works correctly when there are no control characters to remove."""
    text = "Hello World"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello World"


def test_sanitize_input_complex_script_tags():
    """Test that sanitize_input removes complex script tags with attributes and whitespace."""
    text = '<script type="text/javascript" src="malicious.js">alert("XSS")</script>Hello'
    sanitized = sanitize_input(text)
    assert sanitized == "Hello"


def test_sanitize_input_multiple_script_tags():
    """Test that sanitize_input removes multiple script tags."""
    text = '<script>alert(1)</script>Hello<script>alert(2)</script>World'
    sanitized = sanitize_input(text)
    assert sanitized == "HelloWorld"


def test_validate_safe_input_with_safe_input():
    """Test that validate_safe_input returns the input when it's safe."""
    text = "Hello World"
    result = validate_safe_input(text)
    assert result == text


def test_validate_safe_input_raises_with_script():
    """Test that validate_safe_input raises an exception when script tags are present."""
    with pytest.raises(InputSanitizationError) as excinfo:
        validate_safe_input("<script>bad</script>")

    assert "Unsafe input detected" in str(excinfo.value)
    assert "<script>bad</script>" in str(excinfo.value.details)


def test_validate_safe_input_raises_with_control_chars():
    """Test that validate_safe_input raises an exception when control characters are present."""
    with pytest.raises(InputSanitizationError) as excinfo:
        validate_safe_input("Hello\x00World")

    assert "Unsafe input detected" in str(excinfo.value)
    # The control character is escaped in the string representation of the details dictionary
    assert "Hello\\x00World" in str(excinfo.value.details)
