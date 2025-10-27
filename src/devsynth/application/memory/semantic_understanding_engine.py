"""
Semantic Understanding Engine for Enhanced Code Comprehension

This module implements deep semantic analysis that uses execution learning
to understand code behavior beyond syntax, addressing the shallow understanding
problem from the research literature.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .execution_learning_algorithm import ExecutionPattern, PatternLibrary
from ...domain.models.memory import MemeticUnit, MemeticMetadata, MemeticSource, CognitiveType
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class SemanticComponents:
    """Extracted semantic components from code analysis."""
    structural_analysis: Dict[str, Any]
    data_flow_patterns: Dict[str, Any]
    behavioral_intentions: Dict[str, Any]
    execution_mappings: Dict[str, Any]
    semantic_fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "structural_analysis": self.structural_analysis,
            "data_flow_patterns": self.data_flow_patterns,
            "behavioral_intentions": self.behavioral_intentions,
            "execution_mappings": self.execution_mappings,
            "semantic_fingerprint": self.semantic_fingerprint
        }


@dataclass
class BehavioralIntent:
    """Analysis of code behavioral intentions."""
    primary_purpose: str
    algorithmic_patterns: List[str]
    business_logic: Dict[str, Any]
    side_effects: List[str]
    complexity_level: str
    intent_confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "primary_purpose": self.primary_purpose,
            "algorithmic_patterns": self.algorithmic_patterns,
            "business_logic": self.business_logic,
            "side_effects": self.side_effects,
            "complexity_level": self.complexity_level,
            "intent_confidence": self.intent_confidence
        }


class SemanticUnderstandingEngine:
    """Engine for deep semantic understanding of code behavior."""

    def __init__(self, pattern_library: PatternLibrary = None):
        """Initialize the semantic understanding engine."""
        self.pattern_library = pattern_library or PatternLibrary()
        self.understanding_cache: Dict[str, SemanticComponents] = {}
        self.intent_cache: Dict[str, BehavioralIntent] = {}

        logger.info("Semantic understanding engine initialized")

    def extract_semantic_components(self, code: str) -> SemanticComponents:
        """Extract semantic meaning from code beyond syntax."""
        # Check cache first
        code_hash = self._compute_code_hash(code)
        if code_hash in self.understanding_cache:
            return self.understanding_cache[code_hash]

        # Parse AST for structural understanding
        ast_analysis = self._analyze_ast_structure(code)

        # Extract data flow patterns
        data_flow = self._analyze_data_flow(code)

        # Identify behavioral intentions
        behavioral_intent = self._analyze_behavioral_intent(code)

        # Map to execution outcomes using pattern library
        execution_mapping = self._map_to_execution_outcomes(ast_analysis, data_flow, behavioral_intent)

        # Generate semantic fingerprint
        semantic_fingerprint = self._generate_semantic_fingerprint(execution_mapping)

        components = SemanticComponents(
            structural_analysis=ast_analysis,
            data_flow_patterns=data_flow,
            behavioral_intentions=behavioral_intent.to_dict() if behavioral_intent else {},
            execution_mappings=execution_mapping,
            semantic_fingerprint=semantic_fingerprint
        )

        # Cache the result
        self.understanding_cache[code_hash] = components

        return components

    def analyze_behavioral_intent(self, code: str) -> BehavioralIntent:
        """Analyze what the code is intended to accomplish."""
        # Check cache first
        code_hash = self._compute_code_hash(code)
        if code_hash in self.intent_cache:
            return self.intent_cache[code_hash]

        # Identify algorithmic patterns
        algorithm_patterns = self._identify_algorithms(code)

        # Extract business logic intent
        business_logic = self._extract_business_logic(code)

        # Determine side effects and state changes
        side_effects = self._analyze_side_effects(code)

        # Classify complexity and purpose
        complexity_classification = self._classify_complexity(code)

        # Calculate intent confidence
        intent_confidence = self._calculate_intent_confidence(code)

        # Determine primary purpose
        primary_purpose = self._determine_primary_purpose(algorithm_patterns, business_logic)

        intent = BehavioralIntent(
            primary_purpose=primary_purpose,
            algorithmic_patterns=algorithm_patterns,
            business_logic=business_logic,
            side_effects=side_effects,
            complexity_level=complexity_classification,
            intent_confidence=intent_confidence
        )

        # Cache the result
        self.intent_cache[code_hash] = intent

        return intent

    def generate_semantic_fingerprint(self, components: SemanticComponents) -> str:
        """Generate a unique fingerprint representing code semantics."""
        # Combine structural, behavioral, and execution characteristics
        fingerprint_components = [
            components.structural_analysis.get("hash", ""),
            components.data_flow_patterns.get("signature", ""),
            str(components.behavioral_intentions.get("primary_purpose", "")),
            components.execution_mappings.get("outcome_signature", "")
        ]

        # Create composite hash
        composite_string = "|".join(fingerprint_components)
        return self._compute_code_hash(composite_string)

    def detect_semantic_equivalence(self, code1: str, code2: str) -> Dict[str, Any]:
        """Detect if two code snippets are semantically equivalent despite surface differences."""
        # Extract semantic components from both codes
        components1 = self.extract_semantic_components(code1)
        components2 = self.extract_semantic_components(code2)

        # Compare behavioral patterns
        intent1 = self.analyze_behavioral_intent(code1)
        intent2 = self.analyze_behavioral_intent(code2)

        # Calculate semantic similarity
        similarity_score = self._calculate_semantic_similarity(components1, components2)

        # Test with pattern matching
        patterns1 = self.pattern_library.find_matches(components1.to_dict())
        patterns2 = self.pattern_library.find_matches(components2.to_dict())

        pattern_similarity = self._calculate_pattern_similarity(patterns1, patterns2)

        # Calculate behavioral equivalence
        behavioral_equivalence = self._calculate_behavioral_equivalence(intent1, intent2)

        # Overall equivalence assessment
        is_equivalent = (similarity_score > 0.8 and
                        behavioral_equivalence > 0.8 and
                        pattern_similarity > 0.7)

        return {
            "is_equivalent": is_equivalent,
            "similarity_score": similarity_score,
            "behavioral_match": behavioral_equivalence,
            "pattern_similarity": pattern_similarity,
            "semantic_fingerprint_match": components1.semantic_fingerprint == components2.semantic_fingerprint,
            "validation_method": "multi_faceted_semantic_analysis"
        }

    def predict_execution_behavior(self, code: str) -> Dict[str, Any]:
        """Predict execution behavior based on learned patterns."""
        components = self.extract_semantic_components(code)

        # Find matching patterns
        matching_patterns = self.pattern_library.find_matches(components.to_dict())

        if not matching_patterns:
            return {
                "prediction": "unknown_behavior",
                "confidence": 0.0,
                "supporting_patterns": [],
                "reasoning": "No matching patterns found in learned knowledge"
            }

        # Aggregate predictions from matching patterns
        predictions = []
        confidences = []

        for pattern in matching_patterns[:5]:  # Top 5 patterns
            predictions.append(pattern.expected_outcomes)
            confidences.append(pattern.confidence)

        # Calculate aggregate prediction
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Determine most likely outcome
        outcome_types = [p.get("success_rate", 0.5) for p in predictions]
        predicted_success_rate = sum(outcome_types) / len(outcome_types) if outcome_types else 0.5

        return {
            "prediction": "success" if predicted_success_rate > 0.6 else "potential_failure",
            "confidence": avg_confidence,
            "predicted_success_rate": predicted_success_rate,
            "supporting_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "confidence": p.confidence,
                    "expected_outcome": p.expected_outcomes
                }
                for p in matching_patterns[:3]
            ],
            "semantic_analysis": components.to_dict(),
            "reasoning": f"Based on {len(matching_patterns)} matching behavioral patterns"
        }

    def _analyze_ast_structure(self, code: str) -> Dict[str, Any]:
        """Analyze AST structure for semantic understanding."""
        try:
            tree = ast.parse(code)

            # Count different AST node types
            node_counts = defaultdict(int)

            class ASTAnalyzer(ast.NodeVisitor):
                def generic_visit(self, node):
                    node_counts[type(node).__name__] += 1
                    super().generic_visit(node)

            analyzer = ASTAnalyzer()
            analyzer.visit(tree)

            # Extract function and class information
            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line": node.lineno,
                        "complexity": self._calculate_function_complexity(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "line": node.lineno
                    })

            return {
                "node_counts": dict(node_counts),
                "functions": functions,
                "classes": classes,
                "total_lines": len(code.split('\n')),
                "hash": self._compute_code_hash(code)
            }

        except SyntaxError as e:
            return {
                "error": f"SyntaxError: {e.msg}",
                "line": e.lineno,
                "hash": self._compute_code_hash(code)
            }

    def _analyze_data_flow(self, code: str) -> Dict[str, Any]:
        """Analyze data flow patterns in the code."""
        data_flow = {
            "variables": {},
            "dependencies": {},
            "data_transformations": []
        }

        try:
            tree = ast.parse(code)

            # Extract variable usage patterns
            class DataFlowAnalyzer(ast.NodeVisitor):
                def __init__(self):
                    self.variables = {}
                    self.assignments = {}
                    self.references = defaultdict(list)

                def visit_Assign(self, node):
                    if node.targets and hasattr(node.targets[0], 'id'):
                        var_name = node.targets[0].id
                        self.assignments[var_name] = {
                            "line": node.lineno,
                            "type": self._get_expression_type(node.value)
                        }
                        self.variables[var_name] = "assigned"
                    self.generic_visit(node)

                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Load):
                        self.references[node.id].append(node.lineno)
                        if node.id not in self.variables:
                            self.variables[node.id] = "referenced"
                    self.generic_visit(node)

                def _get_expression_type(self, node):
                    if isinstance(node, ast.Str):
                        return "string"
                    elif isinstance(node, ast.Num):
                        return "number"
                    elif isinstance(node, ast.List):
                        return "list"
                    elif isinstance(node, ast.Dict):
                        return "dict"
                    elif isinstance(node, ast.Call):
                        return "function_call"
                    else:
                        return "expression"

            analyzer = DataFlowAnalyzer()
            analyzer.visit(tree)

            data_flow["variables"] = analyzer.variables
            data_flow["assignments"] = analyzer.assignments
            data_flow["references"] = dict(analyzer.references)

        except SyntaxError:
            data_flow["error"] = "Could not analyze data flow due to syntax error"

        return data_flow

    def _analyze_behavioral_intent(self, code: str) -> BehavioralIntent:
        """Analyze what the code is intended to accomplish."""
        # Identify algorithmic patterns
        algorithm_patterns = self._identify_algorithms(code)

        # Extract business logic intent
        business_logic = self._extract_business_logic(code)

        # Determine side effects and state changes
        side_effects = self._analyze_side_effects(code)

        # Classify complexity and purpose
        complexity_classification = self._classify_complexity(code)

        # Calculate intent confidence
        intent_confidence = self._calculate_intent_confidence(code)

        # Determine primary purpose
        primary_purpose = self._determine_primary_purpose(algorithm_patterns, business_logic)

        return BehavioralIntent(
            primary_purpose=primary_purpose,
            algorithmic_patterns=algorithm_patterns,
            business_logic=business_logic,
            side_effects=side_effects,
            complexity_level=complexity_classification,
            intent_confidence=intent_confidence
        )

    def _map_to_execution_outcomes(self, ast_analysis: Dict, data_flow: Dict, behavioral_intent: BehavioralIntent) -> Dict[str, Any]:
        """Map structural analysis to expected execution outcomes."""
        execution_mappings = {
            "expected_behavior": behavioral_intent.primary_purpose,
            "complexity_indicators": {
                "structural_complexity": self._calculate_structural_complexity(ast_analysis),
                "data_flow_complexity": self._calculate_data_flow_complexity(data_flow),
                "algorithmic_complexity": behavioral_intent.complexity_level
            },
            "risk_factors": self._identify_risk_factors(ast_analysis, data_flow, behavioral_intent),
            "performance_characteristics": self._analyze_performance_characteristics(ast_analysis, data_flow),
            "outcome_signature": self._generate_outcome_signature(ast_analysis, data_flow, behavioral_intent)
        }

        return execution_mappings

    def _identify_algorithms(self, code: str) -> List[str]:
        """Identify algorithmic patterns in the code."""
        patterns = []
        code_lower = code.lower()

        # Pattern matching for common algorithms
        algorithm_patterns = {
            "sorting": ["sort", "sorted", "reverse"],
            "searching": ["find", "search", "index", "in"],
            "iteration": ["for", "while", "each"],
            "recursion": ["return", "recursive"],
            "validation": ["if", "check", "validate", "verify"],
            "transformation": ["map", "filter", "transform", "convert"],
            "aggregation": ["sum", "count", "total", "aggregate", "reduce"],
            "comparison": ["compare", "min", "max", "equal"]
        }

        for pattern_name, keywords in algorithm_patterns.items():
            if any(keyword in code_lower for keyword in keywords):
                patterns.append(pattern_name)

        return patterns

    def _extract_business_logic(self, code: str) -> Dict[str, Any]:
        """Extract business logic from code comments and naming."""
        business_context = {
            "domain_indicators": [],
            "purpose_indicators": [],
            "stakeholder_indicators": []
        }

        lines = code.split('\n')

        for line in lines:
            # Check for business domain keywords
            business_domains = [
                "user", "customer", "client", "account", "profile",
                "payment", "transaction", "billing", "invoice",
                "product", "service", "order", "cart",
                "auth", "login", "security", "permission",
                "report", "analytics", "dashboard", "metric"
            ]

            for domain in business_domains:
                if domain in line.lower():
                    business_context["domain_indicators"].append(domain)
                    break

            # Check for purpose indicators
            purpose_words = ["calculate", "process", "validate", "authenticate", "authorize"]
            for purpose in purpose_words:
                if purpose in line.lower():
                    business_context["purpose_indicators"].append(purpose)

        return business_context

    def _analyze_side_effects(self, code: str) -> List[str]:
        """Analyze potential side effects and state changes."""
        side_effects = []

        # Check for I/O operations
        if any(keyword in code.lower() for keyword in ["print", "input", "file", "open", "write", "read"]):
            side_effects.append("io_operations")

        # Check for external calls
        if any(keyword in code.lower() for keyword in ["api", "http", "request", "database", "db"]):
            side_effects.append("external_calls")

        # Check for global state modification
        if any(keyword in code.lower() for keyword in ["global", "class", "static", "singleton"]):
            side_effects.append("global_state")

        # Check for exception handling (indicates side effects)
        if any(keyword in code.lower() for keyword in ["try", "except", "raise", "error"]):
            side_effects.append("exception_handling")

        return side_effects

    def _classify_complexity(self, code: str) -> str:
        """Classify code complexity level."""
        lines = code.strip().split('\n')
        line_count = len(lines)

        # Count complexity indicators
        complexity_score = 0

        # Line count contribution
        complexity_score += min(line_count / 10, 5)  # Cap at 5 points

        # Function/class count
        function_count = code.count('def ')
        class_count = code.count('class ')
        complexity_score += function_count * 0.5
        complexity_score += class_count * 1.0

        # Control structure count
        control_structures = code.count('if ') + code.count('for ') + code.count('while ')
        complexity_score += control_structures * 0.3

        # Nested structure indicators
        nesting_indicators = code.count('    ') + code.count('\t')
        complexity_score += nesting_indicators * 0.1

        # Classify based on score
        if complexity_score < 2:
            return "simple"
        elif complexity_score < 5:
            return "moderate"
        elif complexity_score < 10:
            return "complex"
        else:
            return "very_complex"

    def _calculate_intent_confidence(self, code: str) -> float:
        """Calculate confidence in behavioral intent analysis."""
        confidence_factors = []

        # Code clarity factors
        if len(code.strip().split('\n')) < 50:  # Reasonable length
            confidence_factors.append(0.2)

        # Naming clarity
        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*', code):  # Has meaningful names
            confidence_factors.append(0.2)

        # Comment presence
        if '#' in code or '"""' in code:
            confidence_factors.append(0.3)

        # Structure clarity
        try:
            ast.parse(code)  # Valid syntax
            confidence_factors.append(0.3)
        except SyntaxError:
            confidence_factors.append(-0.2)

        return min(1.0, max(0.0, sum(confidence_factors)))

    def _determine_primary_purpose(self, algorithm_patterns: List[str], business_logic: Dict[str, Any]) -> str:
        """Determine the primary purpose of the code."""
        if not algorithm_patterns and not business_logic.get("domain_indicators"):
            return "utility_function"

        # Prioritize by algorithm patterns
        algorithm_priority = {
            "validation": "validation",
            "transformation": "data_transformation",
            "aggregation": "data_processing",
            "searching": "information_retrieval",
            "sorting": "data_organization"
        }

        for pattern in algorithm_patterns:
            if pattern in algorithm_priority:
                return algorithm_priority[pattern]

        # Fallback to business domain
        domains = business_logic.get("domain_indicators", [])
        if domains:
            return f"{domains[0]}_management"

        return "general_processing"

    def _calculate_structural_complexity(self, ast_analysis: Dict) -> float:
        """Calculate structural complexity from AST analysis."""
        if "error" in ast_analysis:
            return 0.0

        node_counts = ast_analysis.get("node_counts", {})
        total_nodes = sum(node_counts.values())

        # Weight different node types
        complexity_weights = {
            "FunctionDef": 2.0,
            "ClassDef": 3.0,
            "If": 1.0,
            "For": 1.5,
            "While": 1.5,
            "Try": 2.0,
            "Call": 0.5
        }

        weighted_complexity = 0.0
        for node_type, count in node_counts.items():
            weight = complexity_weights.get(node_type, 1.0)
            weighted_complexity += count * weight

        return min(1.0, weighted_complexity / 50)  # Normalize to 0-1 scale

    def _calculate_data_flow_complexity(self, data_flow: Dict) -> float:
        """Calculate data flow complexity."""
        if "error" in data_flow:
            return 0.0

        variables = data_flow.get("variables", {})
        assignments = data_flow.get("assignments", {})
        references = data_flow.get("references", {})

        # Calculate variable lifecycle complexity
        complexity = 0.0

        # Variables with multiple assignments are more complex
        for var_name, changes in references.items():
            if len(changes) > 3:  # Multiple references
                complexity += 0.1

        # Variables with complex assignment types
        for assignment in assignments.values():
            if assignment.get("type") in ["function_call", "expression"]:
                complexity += 0.2

        return min(1.0, complexity)

    def _identify_risk_factors(self, ast_analysis: Dict, data_flow: Dict, behavioral_intent: BehavioralIntent) -> List[str]:
        """Identify potential risk factors in the code."""
        risks = []

        # Structural risks
        if ast_analysis.get("functions"):
            func_count = len(ast_analysis["functions"])
            if func_count > 5:
                risks.append("high_function_count")

        # Data flow risks
        variables = data_flow.get("variables", {})
        uninitialized_vars = [var for var, status in variables.items() if status == "referenced"]
        if uninitialized_vars:
            risks.append("uninitialized_variables")

        # Behavioral risks
        if "external_calls" in behavioral_intent.side_effects:
            risks.append("external_dependencies")

        if "exception_handling" not in behavioral_intent.side_effects:
            risks.append("no_error_handling")

        return risks

    def _analyze_performance_characteristics(self, ast_analysis: Dict, data_flow: Dict) -> Dict[str, Any]:
        """Analyze expected performance characteristics."""
        performance = {
            "expected_complexity": "unknown",
            "memory_usage": "unknown",
            "io_operations": 0,
            "nested_loops": 0
        }

        # Analyze loop nesting
        code_lines = []
        if "functions" in ast_analysis:
            # This is simplified - would need full AST traversal for accurate loop counting
            code_text = str(ast_analysis)
            performance["nested_loops"] = code_text.count("for") + code_text.count("while")

        # Analyze I/O operations
        if "Call" in ast_analysis.get("node_counts", {}):
            performance["io_operations"] = ast_analysis["node_counts"]["Call"]

        return performance

    def _generate_outcome_signature(self, ast_analysis: Dict, data_flow: Dict, behavioral_intent: BehavioralIntent) -> str:
        """Generate signature representing expected execution outcomes."""
        signature_components = [
            behavioral_intent.primary_purpose,
            behavioral_intent.complexity_level,
            str(len(ast_analysis.get("functions", []))),
            str(len(data_flow.get("variables", {}))),
            ",".join(behavioral_intent.side_effects[:3])
        ]

        return self._compute_code_hash("|".join(signature_components))

    def _compute_code_hash(self, code: str) -> str:
        """Compute hash for code content."""
        import hashlib
        return hashlib.sha256(code.encode()).hexdigest()[:16]

    def _calculate_semantic_similarity(self, components1: SemanticComponents, components2: SemanticComponents) -> float:
        """Calculate semantic similarity between two code components."""
        # Compare structural similarity
        structural_sim = self._compare_structural_similarity(
            components1.structural_analysis,
            components2.structural_analysis
        )

        # Compare data flow similarity
        data_flow_sim = self._compare_data_flow_similarity(
            components1.data_flow_patterns,
            components2.data_flow_patterns
        )

        # Compare behavioral similarity
        behavioral_sim = self._compare_behavioral_similarity(
            components1.behavioral_intentions,
            components2.behavioral_intentions
        )

        # Weighted combination
        return (structural_sim * 0.4 + data_flow_sim * 0.3 + behavioral_sim * 0.3)

    def _compare_structural_similarity(self, analysis1: Dict, analysis2: Dict) -> float:
        """Compare structural similarity between AST analyses."""
        if "error" in analysis1 or "error" in analysis2:
            return 0.0

        # Compare function signatures
        functions1 = analysis1.get("functions", [])
        functions2 = analysis2.get("functions", [])

        if not functions1 and not functions2:
            return 1.0  # Both have no functions
        elif not functions1 or not functions2:
            return 0.0  # One has functions, other doesn't

        # Simple comparison of function names
        func_names1 = {f["name"] for f in functions1}
        func_names2 = {f["name"] for f in functions2}

        overlap = len(func_names1.intersection(func_names2))
        union = len(func_names1.union(func_names2))

        return overlap / union if union > 0 else 0.0

    def _compare_data_flow_similarity(self, flow1: Dict, flow2: Dict) -> float:
        """Compare data flow similarity."""
        variables1 = set(flow1.get("variables", {}))
        variables2 = set(flow2.get("variables", {}))

        if not variables1 and not variables2:
            return 1.0
        elif not variables1 or not variables2:
            return 0.0

        overlap = len(variables1.intersection(variables2))
        union = len(variables1.union(variables2))

        return overlap / union if union > 0 else 0.0

    def _compare_behavioral_similarity(self, intent1: Dict, intent2: Dict) -> float:
        """Compare behavioral intention similarity."""
        purpose1 = intent1.get("primary_purpose", "")
        purpose2 = intent2.get("primary_purpose", "")

        if purpose1 == purpose2:
            return 1.0
        elif purpose1 in purpose2 or purpose2 in purpose1:
            return 0.7
        else:
            return 0.3

    def _calculate_behavioral_equivalence(self, intent1: BehavioralIntent, intent2: BehavioralIntent) -> float:
        """Calculate behavioral equivalence between two code snippets."""
        # Compare primary purposes
        purpose_match = 1.0 if intent1.primary_purpose == intent2.primary_purpose else 0.0

        # Compare algorithmic patterns
        patterns1 = set(intent1.algorithmic_patterns)
        patterns2 = set(intent2.algorithmic_patterns)
        pattern_overlap = len(patterns1.intersection(patterns2)) / len(patterns1.union(patterns2)) if patterns1.union(patterns2) else 0.0

        # Compare side effects
        effects1 = set(intent1.side_effects)
        effects2 = set(intent2.side_effects)
        effects_overlap = len(effects1.intersection(effects2)) / len(effects1.union(effects2)) if effects1.union(effects2) else 0.0

        # Weighted combination
        return (purpose_match * 0.5 + pattern_overlap * 0.3 + effects_overlap * 0.2)

    def _calculate_pattern_similarity(self, patterns1: List[ExecutionPattern], patterns2: List[ExecutionPattern]) -> float:
        """Calculate similarity between pattern sets."""
        if not patterns1 and not patterns2:
            return 1.0
        elif not patterns1 or not patterns2:
            return 0.0

        # Compare pattern types
        types1 = {p.pattern_type for p in patterns1}
        types2 = {p.pattern_type for p in patterns2}

        type_overlap = len(types1.intersection(types2)) / len(types1.union(types2)) if types1.union(types2) else 0.0

        # Compare pattern confidences
        confidences1 = [p.confidence for p in patterns1]
        confidences2 = [p.confidence for p in patterns2]

        avg_confidence1 = sum(confidences1) / len(confidences1) if confidences1 else 0.0
        avg_confidence2 = sum(confidences2) / len(confidences2) if confidences2 else 0.0

        confidence_similarity = 1.0 - abs(avg_confidence1 - avg_confidence2)

        return (type_overlap * 0.6 + confidence_similarity * 0.4)

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> str:
        """Calculate complexity of a function."""
        complexity_score = 0

        # Count statements in function body
        complexity_score += len(node.body)

        # Count control structures
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While)):
                complexity_score += 1

        if complexity_score < 5:
            return "simple"
        elif complexity_score < 15:
            return "moderate"
        elif complexity_score < 30:
            return "complex"
        else:
            return "very_complex"
