import unittest
from typing import List, Dict, Any, Optional

from devsynth.domain.interfaces.code_analysis import CodeAnalysisProvider, CodeAnalysisResult, FileAnalysisResult


class TestCodeAnalysisInterface(unittest.TestCase):
    """Test the code analysis interface."""

    def test_code_analysis_result_interface(self):
        """Test that the CodeAnalysisResult interface has the expected attributes."""
        # Create a minimal implementation of CodeAnalysisResult for testing
        class TestResult(CodeAnalysisResult):
            def __init__(self):
                self.files = {}
                self.symbols = {}
                self.dependencies = {}
                self.metrics = {}

            def get_file_analysis(self, file_path: str) -> Optional[FileAnalysisResult]:
                return self.files.get(file_path)

            def get_symbol_references(self, symbol_name: str) -> List[Dict[str, Any]]:
                return self.symbols.get(symbol_name, [])

            def get_dependencies(self, module_name: str) -> List[str]:
                return self.dependencies.get(module_name, [])

            def get_metrics(self) -> Dict[str, Any]:
                return self.metrics

        # Create an instance and verify it implements the interface
        result = TestResult()
        self.assertIsInstance(result, CodeAnalysisResult)
        
        # Test the methods
        self.assertEqual(result.get_file_analysis("test.py"), None)
        self.assertEqual(result.get_symbol_references("TestClass"), [])
        self.assertEqual(result.get_dependencies("test_module"), [])
        self.assertEqual(result.get_metrics(), {})

    def test_file_analysis_result_interface(self):
        """Test that the FileAnalysisResult interface has the expected attributes."""
        # Create a minimal implementation of FileAnalysisResult for testing
        class TestFileResult(FileAnalysisResult):
            def __init__(self):
                self.imports = []
                self.classes = []
                self.functions = []
                self.variables = []
                self.docstring = ""
                self.metrics = {}

            def get_imports(self) -> List[Dict[str, Any]]:
                return self.imports

            def get_classes(self) -> List[Dict[str, Any]]:
                return self.classes

            def get_functions(self) -> List[Dict[str, Any]]:
                return self.functions

            def get_variables(self) -> List[Dict[str, Any]]:
                return self.variables

            def get_docstring(self) -> str:
                return self.docstring

            def get_metrics(self) -> Dict[str, Any]:
                return self.metrics

        # Create an instance and verify it implements the interface
        file_result = TestFileResult()
        self.assertIsInstance(file_result, FileAnalysisResult)
        
        # Test the methods
        self.assertEqual(file_result.get_imports(), [])
        self.assertEqual(file_result.get_classes(), [])
        self.assertEqual(file_result.get_functions(), [])
        self.assertEqual(file_result.get_variables(), [])
        self.assertEqual(file_result.get_docstring(), "")
        self.assertEqual(file_result.get_metrics(), {})

    def test_code_analysis_provider_interface(self):
        """Test that the CodeAnalysisProvider interface has the expected methods."""
        # Create a minimal implementation of CodeAnalysisProvider for testing
        class TestProvider(CodeAnalysisProvider):
            def analyze_file(self, file_path: str) -> FileAnalysisResult:
                return FileAnalysisResult()

            def analyze_directory(self, dir_path: str, recursive: bool = True) -> CodeAnalysisResult:
                return CodeAnalysisResult()

            def analyze_code(self, code: str, file_name: str = "<string>") -> FileAnalysisResult:
                return FileAnalysisResult()

        # This test will fail until the interfaces are implemented
        # Just checking that the class can be instantiated for now
        provider = TestProvider()
        self.assertIsInstance(provider, CodeAnalysisProvider)


if __name__ == "__main__":
    unittest.main()