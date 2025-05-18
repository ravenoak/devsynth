"""
Domain models for code analysis.
"""

from typing import Dict, List, Any, Optional

from devsynth.domain.interfaces.code_analysis import FileAnalysisResult, CodeAnalysisResult


class FileAnalysis(FileAnalysisResult):
    """Implementation of FileAnalysisResult for storing file analysis data."""

    def __init__(
        self,
        imports: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        functions: List[Dict[str, Any]],
        variables: List[Dict[str, Any]],
        docstring: str,
        metrics: Dict[str, Any]
    ):
        """Initialize a FileAnalysis instance.

        Args:
            imports: List of import dictionaries
            classes: List of class dictionaries
            functions: List of function dictionaries
            variables: List of variable dictionaries
            docstring: Module-level docstring
            metrics: Dictionary of metrics
        """
        self._imports = imports
        self._classes = classes
        self._functions = functions
        self._variables = variables
        self._docstring = docstring
        self._metrics = metrics

    def get_imports(self) -> List[Dict[str, Any]]:
        """Get the imports found in the file."""
        return self._imports

    def get_classes(self) -> List[Dict[str, Any]]:
        """Get the classes found in the file."""
        return self._classes

    def get_functions(self) -> List[Dict[str, Any]]:
        """Get the functions found in the file."""
        return self._functions

    def get_variables(self) -> List[Dict[str, Any]]:
        """Get the variables found in the file."""
        return self._variables

    def get_docstring(self) -> str:
        """Get the module-level docstring of the file."""
        return self._docstring

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about the file."""
        return self._metrics


class CodeAnalysis(CodeAnalysisResult):
    """Implementation of CodeAnalysisResult for storing codebase analysis data."""

    def __init__(
        self,
        files: Dict[str, FileAnalysisResult],
        symbols: Dict[str, List[Dict[str, Any]]],
        dependencies: Dict[str, List[str]],
        metrics: Dict[str, Any]
    ):
        """Initialize a CodeAnalysis instance.

        Args:
            files: Dictionary mapping file paths to FileAnalysisResult instances
            symbols: Dictionary mapping symbol names to lists of reference dictionaries
            dependencies: Dictionary mapping module names to lists of dependency module names
            metrics: Dictionary of metrics
        """
        self._files = files
        self._symbols = symbols
        self._dependencies = dependencies
        self._metrics = metrics

    def get_file_analysis(self, file_path: str) -> Optional[FileAnalysisResult]:
        """Get the analysis result for a specific file."""
        return self._files.get(file_path)

    def get_symbol_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Get all references to a symbol in the codebase."""
        return self._symbols.get(symbol_name, [])

    def get_dependencies(self, module_name: str) -> List[str]:
        """Get the dependencies of a module."""
        return self._dependencies.get(module_name, [])

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about the codebase."""
        return self._metrics

    def get_files(self) -> Dict[str, FileAnalysisResult]:
        """Get all files in the codebase."""
        return self._files

    def get_symbols(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all symbols in the codebase."""
        return self._symbols

    def to_dict(self) -> Dict[str, Any]:
        """Convert the CodeAnalysis object to a dictionary representation."""
        return {
            "files": {path: self._serialize_file_analysis(file_analysis) 
                     for path, file_analysis in self._files.items()},
            "symbols": self._symbols,
            "dependencies": self._dependencies,
            "metrics": self._metrics
        }

    def _serialize_file_analysis(self, file_analysis: FileAnalysisResult) -> Dict[str, Any]:
        """Serialize a FileAnalysisResult object to a dictionary."""
        return {
            "imports": file_analysis.get_imports(),
            "classes": file_analysis.get_classes(),
            "functions": file_analysis.get_functions(),
            "variables": file_analysis.get_variables(),
            "docstring": file_analysis.get_docstring(),
            "metrics": file_analysis.get_metrics()
        }
