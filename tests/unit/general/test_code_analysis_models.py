"""
Tests for the code analysis domain models.
"""
import unittest
from typing import List, Dict, Any, Optional
from devsynth.domain.interfaces.code_analysis import CodeAnalysisProvider, CodeAnalysisResult, FileAnalysisResult
from devsynth.domain.models.code_analysis import FileAnalysis, CodeAnalysis


class TestCodeAnalysisModels(unittest.TestCase):
    """Test the code analysis domain models.

ReqID: N/A"""

    def test_file_analysis_implementation_succeeds(self):
        """Test that FileAnalysis correctly implements FileAnalysisResult.

ReqID: N/A"""
        imports = [{'name': 'os', 'path': 'os'}]
        classes = [{'name': 'TestClass', 'methods': ['test_method'],
            'attributes': ['test_attr']}]
        functions = [{'name': 'test_function', 'params': ['param1'],
            'return_type': 'None'}]
        variables = [{'name': 'test_var', 'type': 'str'}]
        docstring = 'Test docstring'
        metrics = {'lines_of_code': 100, 'complexity': 5}
        file_analysis = FileAnalysis(imports=imports, classes=classes,
            functions=functions, variables=variables, docstring=docstring,
            metrics=metrics)
        self.assertIsInstance(file_analysis, FileAnalysisResult)
        self.assertEqual(file_analysis.get_imports(), imports)
        self.assertEqual(file_analysis.get_classes(), classes)
        self.assertEqual(file_analysis.get_functions(), functions)
        self.assertEqual(file_analysis.get_variables(), variables)
        self.assertEqual(file_analysis.get_docstring(), docstring)
        self.assertEqual(file_analysis.get_metrics(), metrics)

    def test_code_analysis_implementation_succeeds(self):
        """Test that CodeAnalysis correctly implements CodeAnalysisResult.

ReqID: N/A"""
        file_analysis = FileAnalysis(imports=[], classes=[], functions=[],
            variables=[], docstring='', metrics={})
        files = {'test.py': file_analysis}
        symbols = {'TestClass': [{'file': 'test.py', 'line': 10, 'column': 5}]}
        dependencies = {'test_module': ['os', 'sys']}
        metrics = {'total_files': 1, 'total_lines': 100}
        code_analysis = CodeAnalysis(files=files, symbols=symbols,
            dependencies=dependencies, metrics=metrics)
        self.assertIsInstance(code_analysis, CodeAnalysisResult)
        self.assertEqual(code_analysis.get_file_analysis('test.py'),
            file_analysis)
        self.assertEqual(code_analysis.get_file_analysis('nonexistent.py'),
            None)
        self.assertEqual(code_analysis.get_symbol_references('TestClass'),
            symbols['TestClass'])
        self.assertEqual(code_analysis.get_symbol_references(
            'NonexistentClass'), [])
        self.assertEqual(code_analysis.get_dependencies('test_module'),
            dependencies['test_module'])
        self.assertEqual(code_analysis.get_dependencies(
            'nonexistent_module'), [])
        self.assertEqual(code_analysis.get_metrics(), metrics)


if __name__ == '__main__':
    unittest.main()
