---
description: Python code style, formatting, and type hint standards
globs:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "scripts/**/*.py"
alwaysApply: false
---

# DevSynth Code Style

## General Principles

- **Readability**: Easy to understand
- **Simplicity**: KISS principle
- **Consistency**: Follow established patterns

## Python Style

### PEP 8 Compliance

All code **must** adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/).

### Formatting Tools

```bash
# Black formatter (line length: 88)
poetry run black .

# isort for import sorting
poetry run isort .

# Verify with flake8
poetry run flake8 src/ tests/
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ["py312"]

[tool.isort]
profile = "black"
line_length = 88
```

### Type Hints (PEP 484)

**All new code must include type hints:**

```python
from typing import Optional, List, Dict

def process_items(
    items: List[str],
    config: Optional[Dict[str, str]] = None
) -> List[str]:
    """Process items with optional configuration.
    
    Args:
        items: List of items to process
        config: Optional configuration dictionary
        
    Returns:
        Processed items list
    """
    result: List[str] = []
    # Implementation
    return result
```

Run type checker:
```bash
poetry run mypy src tests --config-file pyproject.toml
```

### Docstrings (PEP 257)

**All public modules, classes, functions, methods must have docstrings:**

```python
def calculate_score(data: Dict[str, float], threshold: float = 0.5) -> float:
    """Calculate weighted score from data dictionary.
    
    Uses threshold to filter low-confidence values before
    computing the weighted average.
    
    Args:
        data: Dictionary mapping keys to numeric values
        threshold: Minimum confidence threshold (default: 0.5)
        
    Returns:
        Weighted average score as float
        
    Raises:
        ValueError: If data is empty or threshold invalid
        
    Example:
        >>> calculate_score({"a": 0.8, "b": 0.3}, threshold=0.5)
        0.8
    """
    if not data:
        raise ValueError("Data cannot be empty")
    # Implementation
```

Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings) format.

### Import Organization

```python
# Standard library imports
import os
import sys
from typing import List, Optional

# Third-party imports
import pytest
from pydantic import BaseModel

# Local application imports
from devsynth.domain.models import MemoryItem
from devsynth.application.memory import MemorySystem
```

Use absolute imports where possible.

### Naming Conventions

- **Functions/methods/variables**: `snake_case`
- **Classes**: `CapWords` (PascalCase)
- **Constants**: `UPPER_SNAKE_CASE`
- **Protected members**: `_protected_member`
- **Private members**: `__private_member`

```python
# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Classes
class MemorySystem:
    """Memory management system."""
    
    def __init__(self):
        self._cache = {}  # Protected
        self.__internal_state = None  # Private
    
    def store_item(self, item: MemoryItem) -> str:
        """Store memory item."""
        pass
```

### Error Handling

```python
from devsynth.exceptions import DevSynthError

class MemoryNotFoundError(DevSynthError):
    """Raised when memory item not found."""
    pass

def retrieve(item_id: str) -> MemoryItem:
    """Retrieve memory item by ID."""
    try:
        return self._storage[item_id]
    except KeyError:
        raise MemoryNotFoundError(f"Item {item_id} not found")
```

Use custom exceptions inheriting from `DevSynthError`.
Avoid broad `except Exception:` clauses.

### Logging

```python
from devsynth.logging_setup import get_logger

logger = get_logger(__name__)

def process_data(data):
    """Process data with logging."""
    logger.debug(f"Processing {len(data)} items")
    try:
        result = perform_operation(data)
        logger.info("Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

Use centralized logger from `devsynth.logging_setup`.

## Line Length

Maximum 88 characters (Black default).

## Code Quality Checks

```bash
# Format
poetry run black .
poetry run isort .

# Lint
poetry run flake8 src/ tests/

# Type check
poetry run mypy src tests

# All quality checks
poetry run pre-commit run --all-files
```

## Configuration

flake8 configuration in `pyproject.toml`:
```toml
[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
```

## Examples

### Good Code

```python
from typing import List, Optional
from devsynth.domain.models import MemoryItem
from devsynth.logging_setup import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """In-memory storage for memory items.
    
    Provides CRUD operations with automatic ID generation
    and thread-safe access.
    """
    
    def __init__(self) -> None:
        """Initialize empty memory store."""
        self._items: Dict[str, MemoryItem] = {}
        self._lock = threading.Lock()
    
    def store(self, item: MemoryItem) -> str:
        """Store memory item and return ID.
        
        Args:
            item: Memory item to store
            
        Returns:
            Generated item ID
        """
        with self._lock:
            item_id = self._generate_id()
            self._items[item_id] = item
            logger.debug(f"Stored item {item_id}")
            return item_id
```

### Bad Code (avoid)

```python
# Missing type hints
def store(item):
    # Missing docstring
    id=self._gen_id()  # Non-standard spacing
    self.items[id]=item
    return id

# Broad exception handling
try:
    result = process()
except:  # Too broad
    pass  # Silent failure
```

