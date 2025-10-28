import os
import re


def convert_to_numpy_docstring(file_path):
    with open(file_path) as f:
        content = f.read()

    # Replace "Args:" with "Parameters\n----------"
    content = re.sub(r"\s+Args:\s*\n", "\n    Parameters\n    ----------\n", content)

    # Replace "Returns:" with "Returns\n-------"
    content = re.sub(r"\s+Returns:\s*\n", "\n    Returns\n    -------\n", content)

    # Replace "Raises:" with "Raises\n------"
    content = re.sub(r"\s+Raises:\s*\n", "\n    Raises\n    ------\n", content)

    # Format parameters: "param_name: description" to "param_name : type\n        description"
    # This is a simplified version and might need manual adjustment
    param_pattern = re.compile(
        r"(\s+)([a-zA-Z_][a-zA-Z0-9_]*)(: )(.+?)(?=\n\s+[a-zA-Z_]|\n\n|\n    Returns|\n    Raises|$)",
        re.DOTALL,
    )

    def param_replacer(match):
        indent, name, colon, desc = match.groups()
        # Extract type from function signature or use "object" as default
        return f"{indent}{name} : object\n{indent}    {desc.strip()}"

    content = param_pattern.sub(param_replacer, content)

    with open(file_path, "w") as f:
        f.write(content)

    print(f"Converted docstrings in {file_path}")


# Convert docstrings in the fallback.py file (contains retry_with_exponential_backoff)
fallback_path = "src/devsynth/adapters/providers/fallback.py"
if os.path.exists(fallback_path):
    convert_to_numpy_docstring(fallback_path)
else:
    print(f"File not found: {fallback_path}")
    # Try to find the file
    import subprocess

    result = subprocess.run(
        ["find", "src", "-name", "fallback.py"], capture_output=True, text=True
    )
    if result.stdout:
        fallback_path = result.stdout.strip()
        print(f"Found fallback.py at: {fallback_path}")
        convert_to_numpy_docstring(fallback_path)
