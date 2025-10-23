#!/usr/bin/env python3
"""
Automated Rule Generation System

Analyzes codebase patterns and automatically generates new Cursor rules
to improve consistency, quality, and development efficiency.
"""

import ast
import json
import logging
import os
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class CodePattern:
    """Represents a detected code pattern."""
    pattern_type: str
    description: str
    examples: List[str]
    frequency: int
    confidence: float
    suggested_rule: str
    affected_files: List[str]
    impact_score: float  # 0.0 to 1.0


@dataclass
class RuleSuggestion:
    """Represents a suggested new rule."""
    rule_name: str
    description: str
    rule_content: str
    confidence: float
    priority: int
    patterns: List[CodePattern]
    yaml_frontmatter: Dict[str, Any]
    examples: List[str]


class CodebaseAnalyzer:
    """Analyzes codebase to detect patterns and suggest rules."""

    def __init__(self, source_dirs: List[str], exclude_patterns: List[str] = None):
        self.source_dirs = [Path(d) for d in source_dirs]
        self.exclude_patterns = exclude_patterns or [
            "**/__pycache__/**", "**/node_modules/**", "**/.git/**",
            "**/dist/**", "**/build/**", "**/*.pyc", "**/.pytest_cache/**"
        ]
        self.patterns: List[CodePattern] = []

    def analyze_codebase(self) -> List[CodePattern]:
        """Analyze the entire codebase for patterns."""
        patterns = []

        for source_dir in self.source_dirs:
            if not source_dir.exists():
                continue

            patterns.extend(self._analyze_directory(source_dir))

        # Group similar patterns and calculate frequencies
        grouped_patterns = self._group_patterns(patterns)

        return grouped_patterns

    def _analyze_directory(self, directory: Path) -> List[CodePattern]:
        """Analyze a directory for code patterns."""
        patterns = []

        # Analyze Python files
        for py_file in directory.rglob("*.py"):
            if self._should_exclude(py_file):
                continue

            try:
                patterns.extend(self._analyze_python_file(py_file))
            except Exception as e:
                logging.warning(f"Failed to analyze {py_file}: {e}")

        # Analyze Markdown files
        for md_file in directory.rglob("*.md"):
            if self._should_exclude(md_file):
                continue

            try:
                patterns.extend(self._analyze_markdown_file(md_file))
            except Exception as e:
                logging.warning(f"Failed to analyze {md_file}: {e}")

        return patterns

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis."""
        file_str = str(file_path)
        return any(re.search(pattern, file_str) for pattern in self.exclude_patterns)

    def _analyze_python_file(self, file_path: Path) -> List[CodePattern]:
        """Analyze a Python file for patterns."""
        patterns = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse AST for structural analysis
        try:
            tree = ast.parse(content, filename=str(file_path))

            # Detect patterns
            patterns.extend(self._detect_import_patterns(tree, file_path))
            patterns.extend(self._detect_function_patterns(tree, file_path))
            patterns.extend(self._detect_class_patterns(tree, file_path))
            patterns.extend(self._detect_docstring_patterns(tree, file_path))
            patterns.extend(self._detect_error_handling_patterns(tree, file_path))

        except SyntaxError:
            # Analyze as text if AST parsing fails
            patterns.extend(self._analyze_python_text(content, file_path))

        return patterns

    def _analyze_markdown_file(self, file_path: Path) -> List[CodePattern]:
        """Analyze a Markdown file for patterns."""
        patterns = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Detect documentation patterns
        patterns.extend(self._detect_docstring_patterns_markdown(content, file_path))
        patterns.extend(self._detect_specification_patterns(content, file_path))

        return patterns

    def _detect_import_patterns(self, tree: ast.Module, file_path: Path) -> List[CodePattern]:
        """Detect import organization patterns."""
        patterns = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")

        # Analyze import organization
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        for imp in imports:
            if self._is_stdlib_import(imp):
                stdlib_imports.append(imp)
            elif self._is_third_party_import(imp):
                third_party_imports.append(imp)
            else:
                local_imports.append(imp)

        # Check if imports are properly organized
        if imports and not self._imports_well_organized(stdlib_imports, third_party_imports, local_imports):
            patterns.append(CodePattern(
                pattern_type="import_organization",
                description="Import statements not properly organized by type",
                examples=imports[:3],
                frequency=1,
                confidence=0.8,
                suggested_rule="import_organization",
                affected_files=[str(file_path)],
                impact_score=0.7
            ))

        return patterns

    def _detect_function_patterns(self, tree: ast.Module, file_path: Path) -> List[CodePattern]:
        """Detect function definition patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for docstrings
                if not ast.get_docstring(node):
                    patterns.append(CodePattern(
                        pattern_type="missing_docstring",
                        description="Function missing docstring",
                        examples=[f"def {node.name}(...):"],
                        frequency=1,
                        confidence=0.9,
                        suggested_rule="function_docstring_requirement",
                        affected_files=[str(file_path)],
                        impact_score=0.6
                    ))

                # Check function length
                if len(node.body) > 20:
                    patterns.append(CodePattern(
                        pattern_type="long_function",
                        description="Function is too long and should be broken down",
                        examples=[f"def {node.name}(...):  # {len(node.body)} lines"],
                        frequency=1,
                        confidence=0.7,
                        suggested_rule="function_length_limit",
                        affected_files=[str(file_path)],
                        impact_score=0.8
                    ))

        return patterns

    def _detect_class_patterns(self, tree: ast.Module, file_path: Path) -> List[CodePattern]:
        """Detect class definition patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for docstrings
                if not ast.get_docstring(node):
                    patterns.append(CodePattern(
                        pattern_type="missing_class_docstring",
                        description="Class missing docstring",
                        examples=[f"class {node.name}:"],
                        frequency=1,
                        confidence=0.9,
                        suggested_rule="class_docstring_requirement",
                        affected_files=[str(file_path)],
                        impact_score=0.6
                    ))

        return patterns

    def _detect_docstring_patterns(self, tree: ast.Module, file_path: Path) -> List[CodePattern]:
        """Detect docstring patterns and quality."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Check docstring quality
                    if len(docstring.split()) < 5:
                        patterns.append(CodePattern(
                            pattern_type="poor_docstring",
                            description="Docstring is too brief or uninformative",
                            examples=[docstring[:50] + "..."],
                            frequency=1,
                            confidence=0.8,
                            suggested_rule="docstring_quality",
                            affected_files=[str(file_path)],
                            impact_score=0.5
                        ))

        return patterns

    def _detect_error_handling_patterns(self, tree: ast.Module, file_path: Path) -> List[CodePattern]:
        """Detect error handling patterns."""
        patterns = []

        has_try_blocks = any(isinstance(node, ast.Try) for node in ast.walk(tree))

        if not has_try_blocks:
            # Check if file handles external resources or complex operations
            content = open(file_path).read()
            if any(keyword in content.lower() for keyword in ['file', 'database', 'network', 'api', 'http']):
                patterns.append(CodePattern(
                    pattern_type="missing_error_handling",
                    description="Code interacts with external resources but lacks error handling",
                    examples=["External resource usage detected"],
                    frequency=1,
                    confidence=0.8,
                    suggested_rule="error_handling_requirement",
                    affected_files=[str(file_path)],
                    impact_score=0.9
                ))

        return patterns

    def _analyze_python_text(self, content: str, file_path: Path) -> List[CodePattern]:
        """Analyze Python file as text when AST parsing fails."""
        patterns = []

        # Check for debug statements
        if re.search(r'print\(.*debug|import pdb|breakpoint\(\)', content, re.IGNORECASE):
            patterns.append(CodePattern(
                pattern_type="debug_code",
                description="Debug code found in production file",
                examples=["print(...) debug statements", "import pdb"],
                frequency=1,
                confidence=0.9,
                suggested_rule="debug_code_removal",
                affected_files=[str(file_path)],
                impact_score=0.8
            ))

        # Check for TODO/FIXME comments
        todo_matches = re.findall(r'# (TODO|FIXME|XXX):?.*', content, re.IGNORECASE)
        if todo_matches:
            patterns.append(CodePattern(
                pattern_type="todo_comments",
                description="TODO/FIXME comments suggest incomplete work",
                examples=todo_matches[:3],
                frequency=len(todo_matches),
                confidence=0.7,
                suggested_rule="todo_comment_management",
                affected_files=[str(file_path)],
                impact_score=0.6
            ))

        return patterns

    def _detect_docstring_patterns_markdown(self, content: str, file_path: Path) -> List[CodePattern]:
        """Detect documentation patterns in Markdown files."""
        patterns = []

        # Check for inconsistent formatting
        if file_path.suffix == '.md':
            # Check for missing headers
            lines = content.split('\n')
            if len(lines) > 10 and not any(re.match(r'^#', line) for line in lines):
                patterns.append(CodePattern(
                    pattern_type="missing_headers",
                    description="Markdown file lacks proper heading structure",
                    examples=["No headers found in documentation"],
                    frequency=1,
                    confidence=0.8,
                    suggested_rule="markdown_structure",
                    affected_files=[str(file_path)],
                    impact_score=0.5
                ))

        return patterns

    def _detect_specification_patterns(self, content: str, file_path: Path) -> List[CodePattern]:
        """Detect specification file patterns."""
        patterns = []

        if 'specification' in file_path.name.lower():
            # Check for required sections
            required_sections = ['Overview', 'Requirements', 'Implementation']
            missing_sections = []

            for section in required_sections:
                if f'## {section}' not in content and f'# {section}' not in content:
                    missing_sections.append(section)

            if missing_sections:
                patterns.append(CodePattern(
                    pattern_type="incomplete_specification",
                    description=f"Specification missing required sections: {missing_sections}",
                    examples=missing_sections,
                    frequency=1,
                    confidence=0.9,
                    suggested_rule="specification_template",
                    affected_files=[str(file_path)],
                    impact_score=0.7
                ))

        return patterns

    def _is_stdlib_import(self, import_stmt: str) -> bool:
        """Check if import is from standard library."""
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 'typing', 'collections', 'itertools',
            'functools', 're', 'math', 'random', 'uuid', 'pathlib', 'dataclasses'
        }

        # Extract module name from import statement
        match = re.match(r'(?:from\s+)?(\w+)', import_stmt)
        if match:
            module = match.group(1)
            return module in stdlib_modules

        return False

    def _is_third_party_import(self, import_stmt: str) -> bool:
        """Check if import is from third-party packages."""
        # Common third-party packages
        third_party = {
            'numpy', 'pandas', 'requests', 'flask', 'django', 'fastapi',
            'pytest', 'mypy', 'black', 'flake8', 'sqlalchemy', 'alembic'
        }

        match = re.match(r'(?:from\s+)?(\w+)', import_stmt)
        if match:
            module = match.group(1)
            return module in third_party

        return False

    def _imports_well_organized(self, stdlib: List[str], third_party: List[str], local: List[str]) -> bool:
        """Check if imports are well organized."""
        # Should be: stdlib, blank line, third-party, blank line, local
        all_imports = stdlib + third_party + local

        if not all_imports:
            return True

        # Simple heuristic: check for proper separation
        import_text = '\n'.join(all_imports)

        # Look for proper grouping patterns
        if stdlib and third_party and '\n\n' not in import_text:
            return False

        return True

    def _group_patterns(self, patterns: List[CodePattern]) -> List[CodePattern]:
        """Group similar patterns and calculate aggregate metrics."""
        pattern_groups: Dict[str, List[CodePattern]] = defaultdict(list)

        for pattern in patterns:
            pattern_groups[pattern.pattern_type].append(pattern)

        grouped_patterns = []

        for pattern_type, pattern_list in pattern_groups.items():
            if len(pattern_list) == 1:
                grouped_patterns.append(pattern_list[0])
            else:
                # Aggregate similar patterns
                total_frequency = sum(p.frequency for p in pattern_list)
                all_examples = []
                all_files = []

                for p in pattern_list:
                    all_examples.extend(p.examples)
                    all_files.extend(p.affected_files)

                # Calculate weighted confidence
                total_confidence = sum(p.confidence * p.frequency for p in pattern_list)
                avg_confidence = total_confidence / total_frequency if total_frequency > 0 else 0.5

                # Calculate impact score based on frequency and affected files
                unique_files = len(set(all_files))
                impact_score = min(1.0, (total_frequency * 0.1) + (unique_files * 0.01))

                grouped_patterns.append(CodePattern(
                    pattern_type=pattern_type,
                    description=f"Multiple instances of {pattern_type.replace('_', ' ')} pattern",
                    examples=all_examples[:5],  # Keep top 5 examples
                    frequency=total_frequency,
                    confidence=avg_confidence,
                    suggested_rule=pattern_list[0].suggested_rule,
                    affected_files=list(set(all_files)),
                    impact_score=impact_score
                ))

        # Sort by impact score and frequency
        grouped_patterns.sort(key=lambda x: (x.impact_score, x.frequency), reverse=True)

        return grouped_patterns[:20]  # Return top 20 patterns


class RuleGenerator:
    """Generates Cursor rules based on detected patterns."""

    def __init__(self, rules_dir: Path):
        self.rules_dir = rules_dir
        self.rules_dir.mkdir(parents=True, exist_ok=True)

    def generate_rule_from_pattern(self, pattern: CodePattern) -> RuleSuggestion:
        """Generate a Cursor rule from a detected pattern."""

        # Generate rule name
        rule_name = pattern.suggested_rule

        # Generate description
        description = f"Automatically generated rule for {pattern.pattern_type.replace('_', ' ')} pattern"

        # Generate rule content based on pattern type
        rule_content = self._generate_rule_content(pattern)

        # Generate YAML frontmatter
        yaml_frontmatter = {
            "description": description,
            "generated_by": "auto_rule_generator",
            "pattern_type": pattern.pattern_type,
            "confidence": pattern.confidence,
            "alwaysApply": pattern.confidence > 0.8,
            "globs": self._generate_globs(pattern.affected_files)
        }

        # Generate examples
        examples = pattern.examples[:3] if pattern.examples else ["No examples available"]

        return RuleSuggestion(
            rule_name=rule_name,
            description=description,
            rule_content=rule_content,
            confidence=pattern.confidence,
            priority=int(pattern.impact_score * 5),  # Convert to 1-5 scale
            patterns=[pattern],
            yaml_frontmatter=yaml_frontmatter,
            examples=examples
        )

    def _generate_rule_content(self, pattern: CodePattern) -> str:
        """Generate the actual rule content based on pattern type."""
        base_content = f"""# {pattern.pattern_type.replace('_', ' ').title()} Rule

This rule was automatically generated based on detected patterns in the codebase.

## Pattern Description
{pattern.description}

## Impact
- **Frequency**: {pattern.frequency} occurrences
- **Affected Files**: {len(pattern.affected_files)} files
- **Impact Score**: {pattern.impact_score:.2f}

## Examples
"""

        for i, example in enumerate(pattern.examples[:3], 1):
            base_content += f"{i}. {example}\n"

        # Add specific guidance based on pattern type
        if pattern.pattern_type == "import_organization":
            base_content += """

## Import Organization Guidelines

Organize imports in the following order:

1. **Standard Library Imports**
   ```python
   import os
   import sys
   from typing import List, Dict, Optional
   ```

2. **Third-Party Imports**
   ```python
   import numpy as np
   from fastapi import FastAPI
   ```

3. **Local Imports**
   ```python
   from models import User
   from utils import helper_function
   ```

Always separate groups with blank lines and avoid wildcard imports.
"""
        elif pattern.pattern_type == "missing_docstring":
            base_content += """

## Docstring Requirements

All public functions and classes must have comprehensive docstrings:

```python
def calculate_total(items: List[Item]) -> float:
    \"\"\"
    Calculate the total value of items.

    Args:
        items: List of items to calculate total for

    Returns:
        Total value as float

    Raises:
        ValueError: If items list is empty
    \"\"\"
    pass
```
"""
        elif pattern.pattern_type == "debug_code":
            base_content += """

## Debug Code Prevention

Remove debug code before committing:

❌ **Avoid:**
```python
print(f"Debug: {variable}")  # Debug statement
import pdb; pdb.set_trace()  # Breakpoint
```

✅ **Instead:**
```python
logging.debug(f"Processing {variable}")  # Use logging
# Remove debug code entirely
```
"""
        elif pattern.pattern_type == "missing_error_handling":
            base_content += """

## Error Handling Requirements

Always handle potential errors when working with external resources:

```python
# ✅ Good: Proper error handling
try:
    result = external_api_call()
except ConnectionError as e:
    logging.error(f"API connection failed: {e}")
    return default_value
except TimeoutError as e:
    logging.error(f"API timeout: {e}")
    return default_value

# ❌ Avoid: No error handling
result = external_api_call()  # Risky!
```
"""

        return base_content

    def _generate_globs(self, affected_files: List[str]) -> List[str]:
        """Generate appropriate glob patterns for the rule."""
        if not affected_files:
            return ["**/*"]

        # Analyze file extensions and directories
        extensions = set()
        directories = set()

        for file_path in affected_files:
            path = Path(file_path)
            extensions.add(path.suffix)
            directories.add(str(path.parent))

        # Generate globs based on common patterns
        globs = []

        if ".py" in extensions:
            globs.append("**/*.py")

        if ".md" in extensions:
            globs.append("**/*.md")

        # Add specific directory patterns if needed
        for directory in directories:
            if "test" in directory.lower():
                globs.append("**/test*.py")
            elif "spec" in directory.lower():
                globs.append("**/spec*.md")

        return globs if globs else ["**/*"]

    def save_rule_suggestion(self, suggestion: RuleSuggestion, approved: bool = False):
        """Save a rule suggestion for review or immediate use."""
        suggestions_dir = self.rules_dir.parent / "suggestions"
        suggestions_dir.mkdir(exist_ok=True)

        status = "approved" if approved else "pending"
        filename = f"{suggestion.rule_name}_{status}.json"

        suggestion_data = {
            **asdict(suggestion),
            "created_at": suggestion.yaml_frontmatter.pop("created_at", None),
            "status": status
        }

        with open(suggestions_dir / filename, 'w') as f:
            json.dump(suggestion_data, f, indent=2)

        # If approved, also create the actual rule file
        if approved:
            self._create_rule_file(suggestion)

    def _create_rule_file(self, suggestion: RuleSuggestion):
        """Create the actual Cursor rule file."""
        rule_file = self.rules_dir / f"{suggestion.rule_name}.mdc"

        # Create YAML frontmatter
        frontmatter_lines = ["---"]
        for key, value in suggestion.yaml_frontmatter.items():
            if isinstance(value, list):
                frontmatter_lines.append(f"{key}: [{', '.join(f'"{v}"' for v in value)}]")
            else:
                frontmatter_lines.append(f'{key}: {value}')
        frontmatter_lines.append("---")
        frontmatter_lines.append("")

        # Combine with rule content
        full_content = "\n".join(frontmatter_lines) + suggestion.rule_content

        with open(rule_file, 'w') as f:
            f.write(full_content)


def analyze_and_suggest_rules(source_dirs: List[str], rules_dir: str) -> List[RuleSuggestion]:
    """Main function to analyze codebase and suggest rules."""
    analyzer = CodebaseAnalyzer(source_dirs)
    generator = RuleGenerator(Path(rules_dir))

    print(f"🔍 Analyzing codebase in: {source_dirs}")
    patterns = analyzer.analyze_codebase()
    print(f"📊 Found {len(patterns)} patterns")

    suggestions = []
    for pattern in patterns:
        if pattern.confidence > 0.6 and pattern.impact_score > 0.3:
            suggestion = generator.generate_rule_from_pattern(pattern)
            suggestions.append(suggestion)
            generator.save_rule_suggestion(suggestion)

    print(f"💡 Generated {len(suggestions)} rule suggestions")
    return suggestions


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze codebase and generate Cursor rules")
    parser.add_argument("--source", nargs="+", default=["src", "tests"],
                       help="Source directories to analyze")
    parser.add_argument("--rules-dir", default=".cursor/rules",
                       help="Directory to save generated rules")
    parser.add_argument("--min-confidence", type=float, default=0.7,
                       help="Minimum confidence threshold for suggestions")
    parser.add_argument("--auto-approve", action="store_true",
                       help="Automatically approve and create high-confidence rules")

    args = parser.parse_args()

    suggestions = analyze_and_suggest_rules(args.source, args.rules_dir)

    # Filter by confidence
    high_confidence_suggestions = [s for s in suggestions if s.confidence >= args.min_confidence]

    print(f"\n🎯 High-confidence suggestions ({args.min_confidence}+):")
    for i, suggestion in enumerate(high_confidence_suggestions, 1):
        print(f"{i}. {suggestion.rule_name} (confidence: {suggestion.confidence:.2f})")
        print(f"   {suggestion.description}")
        print(f"   Priority: {suggestion.priority}/5")
        print()

    if args.auto_approve:
        print("🚀 Auto-approving high-confidence rules...")
        generator = RuleGenerator(Path(args.rules_dir))
        for suggestion in high_confidence_suggestions:
            generator.save_rule_suggestion(suggestion, approved=True)
        print(f"✅ Created {len(high_confidence_suggestions)} new rules")
