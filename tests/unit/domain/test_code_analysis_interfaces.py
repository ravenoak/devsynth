import unittest

from devsynth.domain.interfaces.code_analysis import (
    CodeAnalysisResult,
    FileAnalysisResult,
    NoopCodeAnalyzer,
    NoopCodeTransformationProvider,
    SimpleCodeAnalysis,
    SimpleFileAnalysis,
    SimpleTransformation,
    TransformationResult,
)


class TestCodeAnalysisInterfaces(unittest.TestCase):
    """Tests for concrete implementations of code analysis interfaces."""

    def test_simple_file_analysis(self) -> None:
        analysis = SimpleFileAnalysis(metrics={"lines": 1})
        self.assertIsInstance(analysis, FileAnalysisResult)
        self.assertEqual(analysis.get_metrics()["lines"], 1)

    def test_noop_analyzer(self) -> None:
        analyzer = NoopCodeAnalyzer()
        result = analyzer.analyze_code("print('hi')")
        self.assertIsInstance(result, FileAnalysisResult)
        self.assertEqual(result.get_metrics()["lines_of_code"], 1)

    def test_noop_transformer(self) -> None:
        transformer = NoopCodeTransformationProvider()
        tresult = transformer.transform_code("a=1")
        self.assertIsInstance(tresult, TransformationResult)
        self.assertEqual(tresult.get_transformed_code(), "a=1")


if __name__ == "__main__":
    unittest.main()
