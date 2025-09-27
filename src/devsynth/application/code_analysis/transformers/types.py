"""Shared type aliases for AST transformer helpers."""

from __future__ import annotations

import ast
from typing import TypeAlias

ClassDefNode: TypeAlias = ast.ClassDef
FunctionDefNode: TypeAlias = ast.FunctionDef
ModuleNode: TypeAlias = ast.Module
StatementList: TypeAlias = list[ast.stmt]
