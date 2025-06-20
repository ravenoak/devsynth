import unittest
from devsynth.application.code_analysis.ast_workflow_integration import AstWorkflowIntegration
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.domain.models.memory import MemoryItem


class MockMemoryStore:
    def __init__(self):
        self.items = {}
        self.counter = 0

    def store(self, item: MemoryItem) -> str:
        self.counter += 1
        item_id = str(self.counter)
        item.id = item_id
        self.items[item_id] = item
        return item_id

    def retrieve(self, item_id: str):
        return self.items.get(item_id)

    def search(self, query, limit=10):
        return list(self.items.values())[:limit]


class TestAstWorkflowIntegration(unittest.TestCase):
    def setUp(self):
        self.memory_manager = MemoryManager({'default': MockMemoryStore()})
        self.integration = AstWorkflowIntegration(self.memory_manager)
        self.analyzer = CodeAnalyzer()

    def test_complexity_and_readability_metrics(self):
        code = """\
\"\"\"Example module\"\"\"

def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

class Calculator:
    \"\"\"Performs calculations.\"\"\"
    def multiply(self, a, b):
        \"\"\"Multiply two numbers.\"\"\"
        return a * b
"""
        analysis = self.analyzer.analyze_code(code)
        complexity = self.integration._calculate_complexity(analysis)
        readability = self.integration._calculate_readability(analysis)
        maintainability = self.integration._calculate_maintainability(analysis)

        self.assertAlmostEqual(complexity, 0.65, places=2)
        self.assertAlmostEqual(readability, 1.0, places=2)
        self.assertAlmostEqual(maintainability, 0.86, places=2)

    def test_differentiate_selects_best_option(self):
        code_no_docs = """\

def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
"""
        code_with_docs = """\
\"\"\"Example module\"\"\"

def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

class Calculator:
    \"\"\"Performs calculations.\"\"\"
    def multiply(self, a, b):
        \"\"\"Multiply two numbers.\"\"\"
        return a * b
"""
        options = [
            {"name": "no_docs", "description": "", "code": code_no_docs},
            {"name": "with_docs", "description": "", "code": code_with_docs},
        ]
        selected = self.integration.differentiate_implementation_quality(options, "task")
        self.assertEqual(selected["name"], "with_docs")
        metrics = selected["metrics"]
        for key in ["complexity", "readability", "maintainability"]:
            self.assertGreaterEqual(metrics[key], 0.0)
            self.assertLessEqual(metrics[key], 1.0)


if __name__ == "__main__":
    unittest.main()
