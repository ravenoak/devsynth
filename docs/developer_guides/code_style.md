# Code Style Guide

This document describes the code style conventions for the DevSynth project.

## Python Style
- Follow [PEP8](https://peps.python.org/pep-0008/) for Python code
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Docstrings should follow the [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html)

## Naming Conventions
- Modules: `snake_case`
- Classes: `CamelCase`
- Functions: `snake_case`
- Constants: `UPPER_CASE`

## Linting
- Use `flake8` for linting
- Run `black .` and `isort .` before submitting code

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for more details.

