from devsynth.security.sanitization import sanitize_input, validate_safe_input
from devsynth.exceptions import InputSanitizationError


def test_sanitize_input_removes_script():
    text = "<script>alert('x')</script>Hello"
    sanitized = sanitize_input(text)
    assert sanitized == "Hello"


def test_validate_safe_input_raises():
    try:
        validate_safe_input("<script>bad</script>")
    except InputSanitizationError:
        assert True
    else:
        assert False
