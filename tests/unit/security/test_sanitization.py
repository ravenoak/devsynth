import pytest

from devsynth.exceptions import InputSanitizationError
from devsynth.security.sanitization import sanitize_input, validate_safe_input


def test_sanitize_input_removes_script_succeeds():
    """Test that sanitize_input removes script tags.

    ReqID: FR-63"""
    text = "<script>alert('x')</script>Hello"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello"


def test_sanitize_input_removes_control_chars_succeeds():
    """Test that sanitize_input removes control characters.

    ReqID: FR-63"""
    text = "Hello\x00World\x1fTest\x7f"
    sanitized = sanitize_input(text)
    assert sanitized == "HelloWorldTest"


def test_sanitize_input_removes_both_succeeds():
    """Test that sanitize_input removes both script tags and control characters.

    ReqID: FR-63"""
    text = "<script>alert('x')\x00</script>Hello\x1fWorld"
    sanitized = sanitize_input(text)
    assert sanitized == "HelloWorld"


def test_sanitize_input_strips_whitespace_succeeds():
    """Test that sanitize_input strips whitespace.

    ReqID: FR-63"""
    text = "  Hello World  "
    sanitized = sanitize_input(text)
    assert sanitized == "Hello World"


def test_sanitize_input_no_script_tags_succeeds():
    """Test that sanitize_input works correctly when there are no script tags to remove.

    ReqID: FR-63"""
    text = "Hello World"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello World"


def test_sanitize_input_no_control_chars_succeeds():
    """Test that sanitize_input works correctly when there are no control characters to remove.

    ReqID: FR-63"""
    text = "Hello World"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello World"


def test_sanitize_input_complex_script_tags_succeeds():
    """Test that sanitize_input removes complex script tags with attributes and whitespace.

    ReqID: FR-63"""
    text = (
        '<script type="text/javascript" src="malicious.js">alert("XSS")</script>Hello'
    )
    sanitized = sanitize_input(text)
    assert sanitized == "Hello"


def test_sanitize_input_multiple_script_tags_succeeds():
    """Test that sanitize_input removes multiple script tags.

    ReqID: FR-63"""
    text = "<script>alert(1)</script>Hello<script>alert(2)</script>World"
    sanitized = sanitize_input(text)
    assert sanitized == "HelloWorld"


def test_validate_safe_input_with_safe_input_returns_expected_result():
    """Test that validate_safe_input returns the input when it's safe.

    ReqID: FR-63"""
    text = "Hello World"
    result = validate_safe_input(text)
    assert result == text


def test_validate_safe_input_raises_with_script_raises_error():
    """Test that validate_safe_input raises an exception when script tags are present.

    ReqID: FR-63"""
    with pytest.raises(InputSanitizationError) as excinfo:
        validate_safe_input("<script>bad</script>")
    assert "Unsafe input detected" in str(excinfo.value)
    assert "<script>bad</script>" in str(excinfo.value.details)


def test_validate_safe_input_raises_with_control_chars_raises_error():
    """Test that validate_safe_input raises an exception when control characters are present.

    ReqID: FR-63"""
    with pytest.raises(InputSanitizationError) as excinfo:
        validate_safe_input("Hello\x00World")
    assert "Unsafe input detected" in str(excinfo.value)
    assert "Hello\\x00World" in str(excinfo.value.details)
