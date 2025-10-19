# Enhanced Docstring Conversion Script

## Overview

This script (`convert_docstrings_v2.py`) is an improved version of the original docstring conversion script. It converts Google-style docstrings to NumPy-style docstrings in Python files while preserving function signatures and avoiding syntax errors.

## Key Improvements

1. **AST-based Parsing**: Uses Python's Abstract Syntax Tree (AST) module to parse and modify docstrings without affecting function signatures or other code.

2. **Preserves Code Structure**: Only modifies docstring nodes in the AST, leaving all other code intact.

3. **Handles Edge Cases**:
   - Properly handles multi-line descriptions
   - Removes duplicate blank lines
   - Handles raw string prefixes (`r"""`)
   - Preserves indentation in multi-line docstrings

4. **Error Handling**: Provides better error handling and reporting when processing files.

5. **Backup Support**: Creates backups of original files before modifying them.

6. **Flexible Output**: Can output to a different file or directory, or overwrite the original.

## Usage

```bash
# Convert a single file
python convert_docstrings_v2.py path/to/file.py

# Convert a single file and output to a different file
python convert_docstrings_v2.py path/to/file.py -o path/to/output.py

# Convert all Python files in a directory
python convert_docstrings_v2.py path/to/directory/

# Convert all Python files in a directory and output to a different directory
python convert_docstrings_v2.py path/to/directory/ -o path/to/output/directory/

# Convert without creating backups
python convert_docstrings_v2.py path/to/file.py --no-backup
```

## Dependencies

- `astor`: Used for converting the modified AST back to source code
  - The script will automatically install this dependency if it's not already installed

## Testing

The script has been tested on multiple files with different docstring patterns and has successfully converted them without introducing syntax errors.

## Example Conversion

### Before:

```python
def my_function(param1, param2):
    """
    This is a function description.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    # Function body
```

### After:

```python
def my_function(param1, param2):
    """
    This is a function description.

    Parameters
    ----------
    param1 : object
        Description of param1
    param2 : object
        Description of param2

    Returns
    -------
    Description of return value
    """
    # Function body
```
