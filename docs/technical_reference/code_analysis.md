---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:
- technical-reference
title: Code Analysis Feature
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; Code Analysis Feature
</div>

# Code Analysis Feature

## Overview

The Code Analysis feature enables DevSynth to analyze Python code and extract information about its structure, including imports, classes, functions, variables, and docstrings. This feature is a foundational component of the Self-Analysis Capabilities phase of the post-MVP roadmap, allowing DevSynth to understand its own codebase and other Python projects.

**Implementation Status:** Core AST parsing and project analysis are implemented. Adapters for external tools are still under development.

## Architecture

The Code Analysis feature follows the hexagonal architecture pattern used throughout DevSynth:

1. **Domain Layer**: Defines interfaces and models for code analysis
   - `CodeAnalysisProvider` interface
   - `CodeAnalysisResult` interface
   - `FileAnalysisResult` interface
   - `FileAnalysis` model
   - `CodeAnalysis` model

2. **Application Layer**: Implements the code analysis logic
   - `CodeAnalyzer` class that implements the `CodeAnalysisProvider` interface
   - `AstVisitor` class that extracts information from Python AST

3. **Adapters Layer**: (Future) Will provide adapters for different code analysis tools

## Usage

### Analyzing a File

```python
from devsynth.application.code_analysis.analyzer import CodeAnalyzer

# Create a code analyzer

analyzer = CodeAnalyzer()

# Analyze a file

result = analyzer.analyze_file("path/to/file.py")

# Access the analysis results

imports = result.get_imports()
classes = result.get_classes()
functions = result.get_functions()
variables = result.get_variables()
docstring = result.get_docstring()
metrics = result.get_metrics()
```

## Analyzing a Directory

```python
from devsynth.application.code_analysis.analyzer import CodeAnalyzer

# Create a code analyzer

analyzer = CodeAnalyzer()

# Analyze a directory

result = analyzer.analyze_directory("path/to/directory")

# Access the analysis results

file_analysis = result.get_file_analysis("path/to/file.py")
symbol_references = result.get_symbol_references("ClassName")
dependencies = result.get_dependencies("module_name")
metrics = result.get_metrics()
```

## Analyzing Code Directly

```python
from devsynth.application.code_analysis.analyzer import CodeAnalyzer

# Create a code analyzer

analyzer = CodeAnalyzer()

# Analyze code

code = """
def hello_world():
    print("Hello, world!")
"""
result = analyzer.analyze_code(code)

# Access the analysis results

functions = result.get_functions()
```

## Data Structures

### FileAnalysisResult

The `FileAnalysisResult` interface provides methods to access information about a single file:

- `get_imports()`: Returns a list of import dictionaries
- `get_classes()`: Returns a list of class dictionaries
- `get_functions()`: Returns a list of function dictionaries
- `get_variables()`: Returns a list of variable dictionaries
- `get_docstring()`: Returns the module-level docstring
- `get_metrics()`: Returns a dictionary of metrics

### CodeAnalysisResult

The `CodeAnalysisResult` interface provides methods to access information about a codebase:

- `get_file_analysis(file_path)`: Returns the `FileAnalysisResult` for a specific file
- `get_symbol_references(symbol_name)`: Returns a list of references to a symbol
- `get_dependencies(module_name)`: Returns a list of dependencies for a module
- `get_metrics()`: Returns a dictionary of metrics

## Implementation Details

The code analysis feature uses Python's built-in `ast` module to parse and analyze Python code. The `AstVisitor` class extends `ast.NodeVisitor` to traverse the abstract syntax tree and extract information about the code structure.

The implementation handles both modern Python style AST nodes (using `ast.Constant`, introduced in Python 3.8) and older style nodes (using `ast.Str`, `ast.Num`, etc.) for backward compatibility, though DevSynth itself requires Python 3.12 or higher.

## Future Enhancements

Future enhancements to the code analysis feature may include:

1. **Dependency Graph Generation**: Visualizing dependencies between modules
2. **Code Quality Metrics**: Calculating metrics like cyclomatic complexity
3. **Code Smell Detection**: Identifying potential issues in the code
4. **Refactoring Suggestions**: Suggesting improvements to the code
5. **Integration with External Tools**: Integrating with tools like Pylint or Black

## Current Limitations

- AST parsing does not yet cover all Python syntax edge cases.
- Adapters for third-party analysis tools are still under development.
