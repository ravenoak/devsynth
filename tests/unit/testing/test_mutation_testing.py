"""
Tests for the mutation testing framework.

This module tests the functionality of devsynth.testing.mutation_testing
to ensure it correctly generates mutations and measures test quality.
"""

import ast
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.testing.mutation_testing import (
    ArithmeticOperatorMutator,
    BooleanOperatorMutator,
    ComparisonOperatorMutator,
    ConstantMutator,
    MutationGenerator,
    MutationReport,
    MutationResult,
    MutationTester,
    UnaryOperatorMutator,
)


@pytest.mark.fast
class TestArithmeticOperatorMutator:
    """Test arithmetic operator mutations."""

    def test_can_mutate_addition(self):
        """Test detection of addition operations."""
        code = "x + y"
        tree = ast.parse(code)
        binop = tree.body[0].value

        mutator = ArithmeticOperatorMutator()
        assert mutator.can_mutate(binop)

    def test_mutates_addition_to_subtraction(self):
        """Test mutation of addition to subtraction."""
        code = "x + y"
        tree = ast.parse(code)
        binop = tree.body[0].value

        mutator = ArithmeticOperatorMutator()
        mutations = list(mutator.mutate(binop))

        assert len(mutations) >= 1
        # Check that at least one mutation changes + to -
        mutation_ops = [type(m.op) for m in mutations]
        assert ast.Sub in mutation_ops

    def test_cannot_mutate_non_arithmetic(self):
        """Test that non-arithmetic operations are not mutated."""
        code = "x == y"
        tree = ast.parse(code)
        compare = tree.body[0].value

        mutator = ArithmeticOperatorMutator()
        assert not mutator.can_mutate(compare)


@pytest.mark.fast
class TestComparisonOperatorMutator:
    """Test comparison operator mutations."""

    def test_can_mutate_equality(self):
        """Test detection of equality operations."""
        code = "x == y"
        tree = ast.parse(code)
        compare = tree.body[0].value

        mutator = ComparisonOperatorMutator()
        assert mutator.can_mutate(compare)

    def test_mutates_equality_to_inequality(self):
        """Test mutation of == to !=."""
        code = "x == y"
        tree = ast.parse(code)
        compare = tree.body[0].value

        mutator = ComparisonOperatorMutator()
        mutations = list(mutator.mutate(compare))

        assert len(mutations) >= 1
        # Check that at least one mutation changes == to !=
        mutation_ops = [type(m.ops[0]) for m in mutations]
        assert ast.NotEq in mutation_ops


@pytest.mark.fast
class TestBooleanOperatorMutator:
    """Test boolean operator mutations."""

    def test_can_mutate_and_operation(self):
        """Test detection of 'and' operations."""
        code = "x and y"
        tree = ast.parse(code)
        boolop = tree.body[0].value

        mutator = BooleanOperatorMutator()
        assert mutator.can_mutate(boolop)

    def test_mutates_and_to_or(self):
        """Test mutation of 'and' to 'or'."""
        code = "x and y"
        tree = ast.parse(code)
        boolop = tree.body[0].value

        mutator = BooleanOperatorMutator()
        mutations = list(mutator.mutate(boolop))

        assert len(mutations) == 1
        assert isinstance(mutations[0].op, ast.Or)


@pytest.mark.fast
class TestUnaryOperatorMutator:
    """Test unary operator mutations."""

    def test_can_mutate_not_operation(self):
        """Test detection of 'not' operations."""
        code = "not x"
        tree = ast.parse(code)
        unaryop = tree.body[0].value

        mutator = UnaryOperatorMutator()
        assert mutator.can_mutate(unaryop)

    def test_mutates_not_by_removal(self):
        """Test mutation of 'not' by removing it."""
        code = "not x"
        tree = ast.parse(code)
        unaryop = tree.body[0].value

        mutator = UnaryOperatorMutator()
        mutations = list(mutator.mutate(unaryop))

        assert len(mutations) == 1
        # The mutation should be just the operand (x)
        assert isinstance(mutations[0], ast.Name)
        assert mutations[0].id == "x"


@pytest.mark.fast
class TestConstantMutator:
    """Test constant mutations."""

    def test_can_mutate_boolean_constant(self):
        """Test detection of boolean constants."""
        code = "True"
        tree = ast.parse(code)
        constant = tree.body[0].value

        mutator = ConstantMutator()
        assert mutator.can_mutate(constant)

    def test_mutates_true_to_false(self):
        """Test mutation of True to False."""
        code = "True"
        tree = ast.parse(code)
        constant = tree.body[0].value

        mutator = ConstantMutator()
        mutations = list(mutator.mutate(constant))

        assert len(mutations) == 1
        assert mutations[0].value == False

    def test_mutates_number_to_zero_and_one(self):
        """Test mutation of numbers."""
        code = "42"
        tree = ast.parse(code)
        constant = tree.body[0].value

        mutator = ConstantMutator()
        mutations = list(mutator.mutate(constant))

        assert len(mutations) == 2
        values = [m.value for m in mutations]
        assert 0 in values
        assert 1 in values


@pytest.mark.fast
class TestMutationGenerator:
    """Test the mutation generator."""

    def test_generates_mutations_for_simple_code(self):
        """Test mutation generation for simple arithmetic."""
        code = """
def add(x, y):
    return x + y
"""

        generator = MutationGenerator()
        mutations = generator.generate_mutations(code, "test.py")

        assert len(mutations) > 0
        # Should have mutations for the + operator
        mutation_ids = [m[0] for m in mutations]
        assert any("test.py" in mid for mid in mutation_ids)

    def test_handles_syntax_errors(self):
        """Test handling of code with syntax errors."""
        code = """
def broken_function(
    # Missing closing parenthesis
    return x + y
"""

        generator = MutationGenerator()
        mutations = generator.generate_mutations(code, "broken.py")

        # Should return empty list for unparseable code
        assert mutations == []

    def test_generates_different_mutation_types(self):
        """Test that different types of mutations are generated."""
        code = """
def complex_function(x, y):
    if x == y:
        return True
    return x + y * 2
"""

        generator = MutationGenerator()
        mutations = generator.generate_mutations(code, "complex.py")

        assert len(mutations) > 5  # Should have multiple mutations

        # Extract mutation snippets to verify variety
        snippets = [m[4] for m in mutations]  # mutated_snippet

        # Should have different types of mutations
        assert len(set(snippets)) > 1


@pytest.mark.fast
class TestMutationTester:
    """Test the main mutation tester."""

    def test_initialization(self):
        """Test mutation tester initialization."""
        tester = MutationTester(timeout_seconds=60)
        assert tester.timeout_seconds == 60
        assert tester.generator is not None

    @patch("subprocess.run")
    def test_run_single_mutation_killed(self, mock_run, tmp_path):
        """Test running a single mutation that gets killed."""
        # Create temporary source file
        source_file = tmp_path / "source.py"
        source_file.write_text("def add(x, y): return x + y")

        # Create temporary test file
        test_file = tmp_path / "test_source.py"
        test_file.write_text(
            """
def test_add():
    from source import add
    assert add(2, 3) == 5
"""
        )

        # Mock test failure (mutation killed)
        mock_result = MagicMock()
        mock_result.returncode = 1  # Test failed
        mock_result.stdout = "FAILED test_source.py::test_add"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        tester = MutationTester()
        result = tester._run_single_mutation(
            source_file,
            "def add(x, y): return x - y",  # Mutated code
            str(test_file),
            "test:1:1",
            1,
            "x + y",
            "x - y",
        )

        assert result.killed == True
        assert result.mutation_id == "test:1:1"
        assert result.line_number == 1
        assert result.original_code == "x + y"
        assert result.mutated_code == "x - y"

    @patch("subprocess.run")
    def test_run_single_mutation_survived(self, mock_run, tmp_path):
        """Test running a single mutation that survives."""
        source_file = tmp_path / "source.py"
        source_file.write_text("def add(x, y): return x + y")

        test_file = tmp_path / "test_source.py"
        test_file.write_text("def test_add(): pass")  # Weak test

        # Mock test success (mutation survived)
        mock_result = MagicMock()
        mock_result.returncode = 0  # Test passed
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        tester = MutationTester()
        result = tester._run_single_mutation(
            source_file,
            "def add(x, y): return x - y",
            str(test_file),
            "test:1:2",
            1,
            "x + y",
            "x - y",
        )

        assert result.killed == False
        assert result.mutation_id == "test:1:2"

    def test_mutation_result_dataclass(self):
        """Test MutationResult dataclass."""
        result = MutationResult(
            mutation_id="test:1:1",
            file_path="test.py",
            line_number=5,
            original_code="x + y",
            mutated_code="x - y",
            mutation_type="arithmetic",
            killed=True,
            test_output="FAILED",
            execution_time=1.5,
        )

        assert result.mutation_id == "test:1:1"
        assert result.killed == True
        assert result.execution_time == 1.5
        assert result.error is None  # Default value

    def test_mutation_report_dataclass(self):
        """Test MutationReport dataclass."""
        mutations = [
            MutationResult(
                "1", "test.py", 1, "x+y", "x-y", "arithmetic", True, "FAILED", 1.0
            ),
            MutationResult(
                "2", "test.py", 2, "x==y", "x!=y", "comparison", False, "PASSED", 1.5
            ),
        ]

        report = MutationReport(
            target_path="src/",
            test_path="tests/",
            total_mutations=2,
            killed_mutations=1,
            survived_mutations=1,
            mutation_score=0.5,
            execution_time=10.0,
            mutations=mutations,
            summary={},
        )

        assert report.total_mutations == 2
        assert report.mutation_score == 0.5
        assert len(report.mutations) == 2


@pytest.mark.fast
def test_integration_mutation_workflow(tmp_path):
    """Test complete mutation testing workflow."""
    # Create a simple source file
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    source_file = source_dir / "calculator.py"
    source_file.write_text(
        """
def add(x, y):
    return x + y

def is_positive(x):
    return x > 0

def is_equal(x, y):
    return x == y
"""
    )

    # Create corresponding tests
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_calculator.py"
    test_file.write_text(
        """
import sys
sys.path.append('../src')
from calculator import add, is_positive, is_equal

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_is_positive():
    assert is_positive(5) == True
    assert is_positive(-5) == False

def test_is_equal():
    assert is_equal(5, 5) == True
    assert is_equal(5, 6) == False
"""
    )

    # Mock subprocess to avoid actually running tests
    with patch("subprocess.run") as mock_run:
        # Simulate that mutations are caught (tests fail)
        mock_result = MagicMock()
        mock_result.returncode = 1  # Test failed (mutation killed)
        mock_result.stdout = "FAILED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        tester = MutationTester(timeout_seconds=5)

        # Run with limited mutations for testing
        report = tester.run_mutations(str(source_dir), str(test_dir), max_mutations=5)

        assert report.target_path == str(source_dir)
        assert report.test_path == str(test_dir)
        assert report.total_mutations <= 5
        assert report.mutation_score >= 0.0
        assert len(report.mutations) == report.total_mutations
