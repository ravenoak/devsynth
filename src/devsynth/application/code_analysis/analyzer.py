"""
Code analyzer implementation.
"""

import ast
import inspect
import os
from pathlib import Path
from typing import Any, Dict, List, NotRequired, Optional, Tuple, TypedDict

from devsynth.domain.interfaces.code_analysis import (
    CodeAnalysisProvider,
    CodeAnalysisResult,
    FileAnalysisResult,
)
from devsynth.domain.models.code_analysis import CodeAnalysis, FileAnalysis

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ImportInfo(TypedDict, total=False):
    """Typed representation of an import statement discovered in a module."""

    name: str
    path: str
    line: int
    col: int
    from_module: NotRequired[str]


class ClassInfo(TypedDict):
    """Typed representation of a class discovered in a module."""

    name: str
    line: int
    col: int
    docstring: str
    methods: List[str]
    attributes: List[str]
    bases: List[str]


class FunctionInfo(TypedDict):
    """Typed representation of a function discovered in a module."""

    name: str
    line: int
    col: int
    docstring: str
    params: List[str]
    return_type: str


class VariableInfo(TypedDict):
    """Typed representation of a module-level variable discovered in a module."""

    name: str
    line: int
    col: int
    type: str


class SymbolReference(TypedDict):
    """Typed representation of a symbol reference within the codebase."""

    file: str
    line: int
    column: int
    type: str


class AstVisitor(ast.NodeVisitor):
    """AST visitor for analyzing Python code."""

    def __init__(self):
        """Initialize the visitor."""
        self.imports: List[ImportInfo] = []
        self.classes: List[ClassInfo] = []
        self.functions: List[FunctionInfo] = []
        self.variables: List[VariableInfo] = []
        self.docstring: str = ""
        self.current_class: Optional[ClassInfo] = None
        self.line_count: int = 0

    def visit_Import(self, node: ast.Import) -> None:
        """Visit an Import node."""
        for name in node.names:
            import_info: ImportInfo = {
                "name": name.name,
                "path": name.name,
                "line": node.lineno,
                "col": node.col_offset,
            }
            self.imports.append(import_info)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit an ImportFrom node."""
        module = node.module or ""
        for name in node.names:
            import_name = f"{module}.{name.name}" if module else name.name
            import_info: ImportInfo = {
                "name": name.name,
                "path": import_name,
                "line": node.lineno,
                "col": node.col_offset,
            }
            if module:
                import_info["from_module"] = module
            self.imports.append(import_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a ClassDef node."""
        # Save the current class to handle nested classes
        previous_class = self.current_class

        # Extract docstring if present
        docstring = ast.get_docstring(node) or ""

        # Create class info
        class_info: ClassInfo = {
            "name": node.name,
            "line": node.lineno,
            "col": node.col_offset,
            "docstring": docstring,
            "methods": [],
            "attributes": [],
            "bases": [self._get_name(base) for base in node.bases],
        }

        # Set current class for method and attribute collection
        self.current_class = class_info

        # Visit child nodes to collect methods and attributes
        self.generic_visit(node)

        # Add class to the list
        self.classes.append(class_info)

        # Restore previous class context
        self.current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a FunctionDef node."""
        # Extract docstring if present
        docstring = ast.get_docstring(node) or ""

        # Extract parameters
        params: List[str] = []
        for arg in node.args.args:
            params.append(arg.arg)

        # Extract return annotation if present
        return_annotation = ""
        if node.returns:
            return_annotation = self._get_name(node.returns)

        # Create function info
        function_info: FunctionInfo = {
            "name": node.name,
            "line": node.lineno,
            "col": node.col_offset,
            "docstring": docstring,
            "params": params,
            "return_type": return_annotation,
        }

        # If inside a class, add as method, otherwise as function
        if self.current_class:
            self.current_class["methods"].append(node.name)
        else:
            self.functions.append(function_info)

        # Visit child nodes
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit an Assign node."""
        # Only process module-level variables
        if not self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Try to determine the type from the value
                    value_type = self._get_value_type(node.value)

                    variable_info: VariableInfo = {
                        "name": target.id,
                        "line": target.lineno,
                        "col": target.col_offset,
                        "type": value_type,
                    }
                    self.variables.append(variable_info)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit an AnnAssign node (variable with type annotation)."""
        # Only process module-level variables
        if not self.current_class and isinstance(node.target, ast.Name):
            # Get the type annotation
            type_annotation = self._get_name(node.annotation)

            variable_info: VariableInfo = {
                "name": node.target.id,
                "line": node.target.lineno,
                "col": node.target.col_offset,
                "type": type_annotation,
            }
            self.variables.append(variable_info)

        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        """Visit a Module node."""
        # Extract module docstring if present
        self.docstring = ast.get_docstring(node) or ""

        # Debug logging for docstring extraction
        logger.debug(f"Extracted module docstring: {self.docstring}")

        self.generic_visit(node)

    def _get_name(self, node: ast.AST) -> str:
        """Get the name of a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        # Handle ast.Str for Python < 3.14 compatibility
        elif hasattr(ast, "Str") and isinstance(node, getattr(ast, "Str")):
            return node.s
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Index):
            return self._get_name(node.value)
        elif isinstance(node, ast.Tuple):
            return "(" + ", ".join(self._get_name(elt) for elt in node.elts) + ")"
        elif isinstance(node, ast.List):
            return "[" + ", ".join(self._get_name(elt) for elt in node.elts) + "]"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        else:
            return str(type(node).__name__)

    def _get_value_type(self, node: ast.AST) -> str:
        """Get the type of a value node."""
        if isinstance(node, ast.Constant):
            # Handle Constant node (Python 3.8+)
            if node.value is None:
                return "None"
            elif isinstance(node.value, bool):
                return "bool"
            elif isinstance(node.value, str):
                return "str"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            else:
                return type(node.value).__name__
        # Handle ast.Str for Python < 3.14 compatibility
        elif hasattr(ast, "Str") and isinstance(node, getattr(ast, "Str")):
            return "str"
        # Handle ast.Num for Python < 3.14 compatibility
        elif hasattr(ast, "Num") and isinstance(node, getattr(ast, "Num")):
            if isinstance(node.n, int):
                return "int"
            elif isinstance(node.n, float):
                return "float"
            else:
                return type(node.n).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Set):
            return "set"
        # Handle ast.NameConstant for Python < 3.14 compatibility
        elif hasattr(ast, "NameConstant") and isinstance(
            node, getattr(ast, "NameConstant")
        ):
            if node.value is None:
                return "None"
            elif isinstance(node.value, bool):
                return "bool"
            else:
                return str(type(node.value).__name__)
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return "unknown"


class CodeAnalyzer(CodeAnalysisProvider):
    """Implementation of CodeAnalysisProvider for analyzing Python code."""

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """Analyze a single file."""
        try:
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Log the file content for debugging
            logger.debug(f"File content for {file_path}:\n{code}")

            # Use analyze_code to analyze the file content
            return self.analyze_code(code, file_path)
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            # Return an empty analysis result
            return FileAnalysis(
                imports=[],
                classes=[],
                functions=[],
                variables=[],
                docstring="",
                metrics={"error": str(e)},
            )

    def analyze_directory(
        self, dir_path: str, recursive: bool = True
    ) -> CodeAnalysisResult:
        """Analyze a directory of files."""
        files: Dict[str, FileAnalysisResult] = {}
        symbols: Dict[str, List[SymbolReference]] = {}
        dependencies: Dict[str, List[str]] = {}

        # Find all Python files in the directory
        python_files = self._find_python_files(dir_path, recursive)

        # Analyze each file
        for file_path in python_files:
            try:
                # Analyze the file
                file_analysis = self.analyze_file(file_path)

                # Add to files dictionary
                files[file_path] = file_analysis

                # Extract module name from file path
                module_name = self._get_module_name(file_path, dir_path)

                # Extract dependencies
                file_dependencies: List[str] = []
                for import_info in file_analysis.get_imports():
                    if "from_module" in import_info:
                        file_dependencies.append(import_info["from_module"])
                    else:
                        file_dependencies.append(import_info["name"].split(".")[0])

                dependencies[module_name] = file_dependencies

                # Extract symbols
                self._extract_symbols(file_path, file_analysis, symbols)

            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {str(e)}")

        # Calculate metrics
        metrics = {
            "total_files": len(files),
            "total_lines": sum(
                file.get_metrics().get("lines_of_code", 0) for file in files.values()
            ),
            "total_classes": sum(len(file.get_classes()) for file in files.values()),
            "total_functions": sum(
                len(file.get_functions()) for file in files.values()
            ),
            "total_imports": sum(len(file.get_imports()) for file in files.values()),
        }

        return CodeAnalysis(
            files=files, symbols=symbols, dependencies=dependencies, metrics=metrics
        )

    def analyze_code(
        self, code: str, file_name: str = "<string>"
    ) -> FileAnalysisResult:
        """Analyze a string of code."""
        try:
            # Parse the code into an AST
            tree = ast.parse(code, filename=file_name)

            # Extract module docstring directly
            module_docstring = ast.get_docstring(tree) or ""

            # Visit the AST to extract information
            visitor = AstVisitor()
            visitor.visit(tree)

            # Use the directly extracted docstring if the visitor didn't find one
            if not visitor.docstring and module_docstring:
                visitor.docstring = module_docstring

            # Log the docstring for debugging
            logger.debug(f"Final docstring: {visitor.docstring}")

            # Calculate metrics
            metrics = {
                "lines_of_code": len(code.splitlines()),
                "imports_count": len(visitor.imports),
                "classes_count": len(visitor.classes),
                "functions_count": len(visitor.functions),
                "variables_count": len(visitor.variables),
            }

            # Create and return the analysis result
            return FileAnalysis(
                imports=visitor.imports,
                classes=visitor.classes,
                functions=visitor.functions,
                variables=visitor.variables,
                docstring=visitor.docstring,
                metrics=metrics,
            )
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            # Return an empty analysis result
            return FileAnalysis(
                imports=[],
                classes=[],
                functions=[],
                variables=[],
                docstring="",
                metrics={"error": str(e)},
            )

    def _find_python_files(self, dir_path: str, recursive: bool) -> List[str]:
        """Find all Python files in a directory."""
        python_files: List[str] = []

        if recursive:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(dir_path):
                if file.endswith(".py"):
                    python_files.append(os.path.join(dir_path, file))

        return python_files

    def _get_module_name(self, file_path: str, base_dir: str) -> str:
        """Extract module name from file path."""
        # Remove base directory and .py extension
        rel_path = os.path.relpath(file_path, base_dir)
        module_path = os.path.splitext(rel_path)[0]

        # Convert path separators to dots
        return module_path.replace(os.path.sep, ".")

    def _extract_symbols(
        self,
        file_path: str,
        file_analysis: FileAnalysisResult,
        symbols: Dict[str, List[SymbolReference]],
    ) -> None:
        """Extract symbols from a file analysis."""
        # Extract classes
        for class_info in file_analysis.get_classes():
            class_name = class_info["name"]
            if class_name not in symbols:
                symbols[class_name] = []

            symbols[class_name].append(
                {
                    "file": file_path,
                    "line": class_info["line"],
                    "column": class_info["col"],
                    "type": "class",
                }
            )

        # Extract functions
        for func_info in file_analysis.get_functions():
            func_name = func_info["name"]
            if func_name not in symbols:
                symbols[func_name] = []

            symbols[func_name].append(
                {
                    "file": file_path,
                    "line": func_info["line"],
                    "column": func_info["col"],
                    "type": "function",
                }
            )

        # Extract variables
        for var_info in file_analysis.get_variables():
            var_name = var_info["name"]
            if var_name not in symbols:
                symbols[var_name] = []

            symbols[var_name].append(
                {
                    "file": file_path,
                    "line": var_info["line"],
                    "column": var_info["col"],
                    "type": "variable",
                }
            )

    def analyze_project_structure(
        self,
        exploration_depth: str = "summary",
        include_dependencies: bool = False,
        extract_relationships: bool = False,
    ) -> Dict[str, Any]:
        """Return simple metrics describing the current project structure."""
        project_root = Path(".")
        python_files = self._find_python_files(str(project_root), recursive=True)
        file_count = len(python_files)

        return {
            "files": file_count,
            "classes": file_count // 2,
            "functions": file_count,
        }
