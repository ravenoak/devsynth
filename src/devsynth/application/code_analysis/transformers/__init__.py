"""Specialised AST transformer helpers for DevSynth."""

from .classes import (
    ClassExtractionRequest,
    FunctionToClassExtractor,
    GeneratedClass,
    build_class_from_functions,
)
from .docstrings import (
    DocstringAdder,
    DocstringMutationResult,
    DocstringSpec,
    apply_docstring_spec,
)
from .methods import (
    FunctionToMethodConverter,
    MethodConversionPlan,
    MethodDefinition,
    MethodType,
    build_method_from_function,
)
from .types import ClassDefNode, FunctionDefNode, ModuleNode, StatementList

__all__ = [
    "ClassDefNode",
    "FunctionDefNode",
    "ModuleNode",
    "StatementList",
    "DocstringAdder",
    "DocstringMutationResult",
    "DocstringSpec",
    "apply_docstring_spec",
    "MethodType",
    "MethodConversionPlan",
    "MethodDefinition",
    "build_method_from_function",
    "FunctionToMethodConverter",
    "ClassExtractionRequest",
    "GeneratedClass",
    "build_class_from_functions",
    "FunctionToClassExtractor",
]
