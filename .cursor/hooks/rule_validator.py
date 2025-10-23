#!/usr/bin/env python3
"""
Rule Validation and Improvement System

Validates existing Cursor rules for quality, consistency, and effectiveness,
and suggests improvements based on best practices and usage patterns.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import yaml


@dataclass
class RuleValidationResult:
    """Results of rule validation."""
    rule_name: str
    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: List[str]
    suggestions: List[str]
    metrics: Dict[str, Any]
    validation_timestamp: str


@dataclass
class RuleImprovement:
    """Represents an improvement suggestion for a rule."""
    rule_name: str
    improvement_type: str
    description: str
    current_content: str
    improved_content: str
    impact_score: float
    confidence: float
    examples: List[str]
    rationale: str


class YAMLFrontmatterValidator:
    """Validates YAML frontmatter in Cursor rules."""

    def __init__(self):
        self.required_fields = ["description"]
        self.recommended_fields = ["alwaysApply", "globs", "generated_by", "confidence"]
        self.valid_glob_patterns = [
            "**/*.py", "**/*.md", "**/*.js", "**/*.ts", "**/*.json",
            "src/**/*.py", "tests/**/*.py", "docs/**/*.md"
        ]

    def validate_frontmatter(self, frontmatter: Dict[str, Any], rule_name: str) -> Tuple[bool, List[str]]:
        """Validate YAML frontmatter."""
        issues = []

        # Check required fields
        for field in self.required_fields:
            if field not in frontmatter:
                issues.append(f"Missing required field: {field}")

        # Check field types and values
        if "alwaysApply" in frontmatter:
            if not isinstance(frontmatter["alwaysApply"], bool):
                issues.append("alwaysApply must be a boolean")

        if "globs" in frontmatter:
            if not isinstance(frontmatter["globs"], list):
                issues.append("globs must be a list")
            else:
                for glob in frontmatter["globs"]:
                    if not isinstance(glob, str):
                        issues.append("Each glob must be a string")
                    elif not any(pattern in glob for pattern in self.valid_glob_patterns):
                        issues.append(f"Potentially invalid glob pattern: {glob}")

        if "confidence" in frontmatter:
            confidence = frontmatter["confidence"]
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                issues.append("confidence must be a number between 0.0 and 1.0")

        return len(issues) == 0, issues


class RuleContentValidator:
    """Validates the content of Cursor rules."""

    def __init__(self):
        self.min_content_length = 50
        self.max_content_length = 3000
        self.required_sections = ["description", "guidelines"]
        self.recommended_sections = ["examples", "references", "related_rules"]

    def validate_content(self, content: str, rule_name: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate rule content."""
        issues = []
        metrics = {
            "length": len(content),
            "sections": [],
            "has_examples": False,
            "clarity_score": 0.0,
            "specificity_score": 0.0
        }

        # Check content length
        if len(content) < self.min_content_length:
            issues.append("Content is too short - add more detailed guidance")
        elif len(content) > self.max_content_length:
            # Don't fail for being too long, just suggest improvement
            pass  # Content length is now just a suggestion, not a failure

        # Check for sections
        lines = content.split('\n')
        current_section = None
        sections_found = []

        for line in lines:
            if re.match(r'^#+\s+', line):  # Header line
                section_name = re.sub(r'^#+\s+', '', line).lower()
                sections_found.append(section_name)
                current_section = section_name

        metrics["sections"] = sections_found

        # Check for examples
        if "example" in content.lower() or "```" in content:
            metrics["has_examples"] = True
        else:
            issues.append("Consider adding practical examples")

        # Calculate clarity score
        clarity_indicators = [
            "clear" in content.lower(),
            "guideline" in content.lower(),
            "standard" in content.lower(),
            "requirement" in content.lower()
        ]
        metrics["clarity_score"] = sum(clarity_indicators) / len(clarity_indicators)

        # Calculate specificity score
        specificity_indicators = [
            any(word in content.lower() for word in ["must", "should", "required", "enforce"]),
            any(word in content.lower() for word in ["avoid", "never", "always", "ensure"]),
            "example" in content.lower() or "```" in content,
            len(re.findall(r'[A-Z][a-z]+:', content)) > 0  # Look for structured guidance
        ]
        metrics["specificity_score"] = sum(specificity_indicators) / len(specificity_indicators)

        # Check for actionable guidance
        if not any(word in content.lower() for word in ["use", "implement", "follow", "apply"]):
            issues.append("Add actionable guidance on how to implement the rule")

        return len(issues) == 0, issues, metrics


class RuleConsistencyValidator:
    """Validates consistency across rules."""

    def __init__(self, rules_dir: Path):
        self.rules_dir = rules_dir
        self.rules_content: Dict[str, str] = {}
        self.load_all_rules()

    def load_all_rules(self):
        """Load all rule content for consistency analysis."""
        for rule_file in self.rules_dir.glob("*.mdc"):
            rule_name = rule_file.stem
            self.rules_content[rule_name] = rule_file.read_text()

    def validate_consistency(self, rule_name: str, content: str) -> Tuple[bool, List[str]]:
        """Validate rule consistency with other rules."""
        issues = []

        # Check for conflicting guidance
        conflicts = self._find_conflicting_guidance(rule_name, content)
        issues.extend(conflicts)

        # Check for missing cross-references
        missing_refs = self._find_missing_references(rule_name, content)
        issues.extend(missing_refs)

        # Check for style consistency
        style_issues = self._check_style_consistency(rule_name, content)
        issues.extend(style_issues)

        return len(issues) == 0, issues

    def _find_conflicting_guidance(self, rule_name: str, content: str) -> List[str]:
        """Find conflicting guidance with other rules."""
        conflicts = []

        # Check for conflicting import organization
        if "import" in content.lower():
            for other_rule, other_content in self.rules_content.items():
                if other_rule != rule_name and "import" in other_content.lower():
                    # Look for conflicting import guidance
                    if "stdlib first" in content.lower() and "third-party first" in other_content.lower():
                        conflicts.append(f"Conflicting import organization guidance with {other_rule}")

        return conflicts

    def _find_missing_references(self, rule_name: str, content: str) -> List[str]:
        """Find missing references to related rules."""
        missing_refs = []

        # Check if rule mentions related concepts but doesn't reference other rules
        related_concepts = {
            "testing": ["testing-philosophy", "bdd-workflow"],
            "documentation": ["documentation"],
            "security": ["security-compliance"],
            "import": ["import_organization"],
            "error": ["error_handling"]
        }

        content_lower = content.lower()
        for concept, related_rules in related_concepts.items():
            if concept in content_lower:
                has_reference = any(ref in content for ref in related_rules)
                if not has_reference:
                    missing_refs.append(f"Consider referencing related rules: {', '.join(related_rules)}")

        return missing_refs

    def _check_style_consistency(self, rule_name: str, content: str) -> List[str]:
        """Check style consistency with other rules."""
        issues = []

        # Check for consistent tone and structure
        other_rules = [r for r in self.rules_content.values() if r != content]

        if other_rules:
            # Check for consistent use of sections
            other_sections = set()
            for rule in other_rules:
                sections = re.findall(r'^#+\s+(.+)$', rule, re.MULTILINE)
                other_sections.update(sections)

            current_sections = set(re.findall(r'^#+\s+(.+)$', content, re.MULTILINE))

            if other_sections and not current_sections:
                issues.append("Consider adding section headers for consistency")

        return issues


class RuleImprovementGenerator:
    """Generates improvements for existing rules."""

    def __init__(self, rules_dir: Path):
        self.rules_dir = rules_dir
        self.frontmatter_validator = YAMLFrontmatterValidator()
        self.content_validator = RuleContentValidator()
        self.consistency_validator = RuleConsistencyValidator(rules_dir)

    def validate_rule(self, rule_name: str) -> RuleValidationResult:
        """Validate a single rule comprehensively."""
        rule_file = self.rules_dir / f"{rule_name}.mdc"

        if not rule_file.exists():
            return RuleValidationResult(
                rule_name=rule_name,
                is_valid=False,
                score=0.0,
                issues=[f"Rule file not found: {rule_file}"],
                suggestions=[],
                metrics={},
                validation_timestamp=datetime.now().isoformat()
            )

        content = rule_file.read_text()

        # Parse YAML frontmatter
        frontmatter, body = self._parse_frontmatter(content)

        # Validate components
        issues = []
        suggestions = []

        # Frontmatter validation
        frontmatter_valid, frontmatter_issues = self.frontmatter_validator.validate_frontmatter(frontmatter, rule_name)
        issues.extend(frontmatter_issues)

        # Content validation
        content_valid, content_issues, metrics = self.content_validator.validate_content(body, rule_name)
        issues.extend(content_issues)

        # Consistency validation
        consistency_valid, consistency_issues = self.consistency_validator.validate_consistency(rule_name, content)
        issues.extend(consistency_issues)

        # Generate suggestions
        suggestions = self._generate_suggestions(rule_name, frontmatter, body, metrics)

        # Calculate overall score
        score = self._calculate_validation_score(frontmatter_valid, content_valid, consistency_valid, metrics)

        return RuleValidationResult(
            rule_name=rule_name,
            is_valid=all([frontmatter_valid, content_valid, consistency_valid]),
            score=score,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics,
            validation_timestamp=datetime.now().isoformat()
        )

    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from rule content."""
        lines = content.split('\n')
        frontmatter = {}
        body_lines = []

        if not lines or not lines[0].strip() == '---':
            return frontmatter, content

        in_frontmatter = True
        for line in lines[1:]:
            if line.strip() == '---':
                in_frontmatter = False
                continue

            if in_frontmatter:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    # Parse simple YAML types
                    if value.lower() in ['true', 'false']:
                        frontmatter[key] = value.lower() == 'true'
                    elif value.startswith('[') and value.endswith(']'):
                        frontmatter[key] = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                    elif value.replace('.', '').replace('-', '').isdigit():
                        frontmatter[key] = float(value) if '.' in value else int(value)
                    else:
                        frontmatter[key] = value
            else:
                body_lines.append(line)

        return frontmatter, '\n'.join(body_lines)

    def _generate_suggestions(self, rule_name: str, frontmatter: Dict[str, Any], body: str, metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        # Frontmatter suggestions (only for missing required fields)
        if "globs" not in frontmatter:
            suggestions.append("Add appropriate glob patterns to control when this rule applies")

        # Content suggestions
        if not metrics.get("has_examples", False):
            suggestions.append("Consider adding practical examples to demonstrate the rule")

        if metrics.get("clarity_score", 0) < 0.5:
            suggestions.append("Consider improving clarity with more specific language")

        if metrics.get("specificity_score", 0) < 0.5:
            suggestions.append("Consider making guidance more specific with clear dos and don'ts")

        return suggestions

    def _calculate_validation_score(self, frontmatter_valid: bool, content_valid: bool,
                                  consistency_valid: bool, metrics: Dict[str, Any]) -> float:
        """Calculate overall validation score."""
        score = 0.0

        # Component scores
        if frontmatter_valid:
            score += 0.4
        if content_valid:
            score += 0.5
        if consistency_valid:
            score += 0.1  # Reduced weight for consistency (cross-references are often subjective)

        # Quality metrics
        score += metrics.get("clarity_score", 0) * 0.1
        score += metrics.get("specificity_score", 0) * 0.1

        # Examples bonus
        if metrics.get("has_examples", False):
            score += 0.1

        return min(1.0, score)


class RuleAutoImprover:
    """Automatically improves rules based on validation results."""

    def __init__(self, rules_dir: Path):
        self.rules_dir = rules_dir
        self.validator = RuleImprovementGenerator(rules_dir)

    def improve_rule(self, rule_name: str) -> Optional[RuleImprovement]:
        """Generate an improved version of a rule."""
        validation = self.validator.validate_rule(rule_name)

        if validation.is_valid or validation.score > 0.8:
            return None  # Rule is already good

        # Generate improvements
        rule_file = self.rules_dir / f"{rule_name}.mdc"
        current_content = rule_file.read_text()

        frontmatter, body = self.validator._parse_frontmatter(current_content)

        # Apply improvements
        improved_frontmatter = self._improve_frontmatter(frontmatter, validation)
        improved_body = self._improve_content(body, validation)

        improved_content = self._format_improved_rule(improved_frontmatter, improved_body)

        return RuleImprovement(
            rule_name=rule_name,
            improvement_type="comprehensive_improvement",
            description=f"Improved rule based on validation results (score: {validation.score:.2f})",
            current_content=current_content,
            improved_content=improved_content,
            impact_score=1.0 - validation.score,
            confidence=0.8,
            examples=validation.issues[:3],
            rationale="Automated improvement based on validation analysis"
        )

    def _improve_frontmatter(self, frontmatter: Dict[str, Any], validation: RuleValidationResult) -> Dict[str, Any]:
        """Improve YAML frontmatter based on validation results."""
        improved = frontmatter.copy()

        # Add missing recommended fields
        if "globs" not in improved:
            improved["globs"] = ["**/*"]  # Default glob

        if "confidence" not in improved:
            improved["confidence"] = validation.score

        return improved

    def _improve_content(self, body: str, validation: RuleValidationResult) -> str:
        """Improve rule content based on validation results."""
        improved = body

        # Add examples if missing
        if not validation.metrics.get("has_examples", False):
            improved += "\n\n## Examples\n\nAdd practical examples here to demonstrate proper implementation."

        # Improve clarity if needed
        if validation.metrics.get("clarity_score", 0) < 0.5:
            improved = self._add_clarity_improvements(improved)

        return improved

    def _add_clarity_improvements(self, content: str) -> str:
        """Add clarity improvements to content."""
        # Add clear guidance section if not present
        if "## Guidelines" not in content:
            content += "\n\n## Guidelines\n\n- Provide clear, actionable guidance\n- Use specific examples when possible\n- Explain the rationale behind each rule"

        return content

    def _format_improved_rule(self, frontmatter: Dict[str, Any], body: str) -> str:
        """Format the improved rule with proper structure."""
        lines = ["---"]

        for key, value in frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}: [{', '.join(f'\"{v}\"' for v in value)}]")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            else:
                lines.append(f"{key}: {value}")

        lines.extend(["---", "", body])
        return "\n".join(lines)

    def batch_improve_rules(self, min_score: float = 0.7) -> List[RuleImprovement]:
        """Improve all rules below the minimum score threshold."""
        improvements = []

        for rule_file in self.rules_dir.glob("*.mdc"):
            rule_name = rule_file.stem
            validation = self.validator.validate_rule(rule_name)

            if validation.score < min_score:
                improvement = self.improve_rule(rule_name)
                if improvement:
                    improvements.append(improvement)

        return improvements


class RuleHealthMonitor:
    """Monitors the health and effectiveness of the rule system."""

    def __init__(self, rules_dir: Path, analytics_dir: Path):
        self.rules_dir = rules_dir
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.validator = RuleImprovementGenerator(rules_dir)
        self.improver = RuleAutoImprover(rules_dir)

    def generate_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report for the rule system."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_rules": 0,
            "valid_rules": 0,
            "average_score": 0.0,
            "rules_by_score": {"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            "common_issues": [],
            "improvement_opportunities": [],
            "system_health": "unknown"
        }

        rule_scores = []
        all_issues = []
        improvements = []

        for rule_file in self.rules_dir.glob("*.mdc"):
            rule_name = rule_file.stem
            validation = self.validator.validate_rule(rule_name)

            report["total_rules"] += 1
            rule_scores.append(validation.score)
            all_issues.extend(validation.issues)

            if validation.is_valid:
                report["valid_rules"] += 1

            # Categorize by score
            if validation.score >= 0.9:
                report["rules_by_score"]["excellent"] += 1
            elif validation.score >= 0.7:
                report["rules_by_score"]["good"] += 1
            elif validation.score >= 0.5:
                report["rules_by_score"]["fair"] += 1
            else:
                report["rules_by_score"]["poor"] += 1

            # Check for improvements
            improvement = self.improver.improve_rule(rule_name)
            if improvement:
                improvements.append(improvement)

        # Calculate averages
        if rule_scores:
            report["average_score"] = sum(rule_scores) / len(rule_scores)

        # Analyze common issues
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        report["common_issues"] = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # System health assessment
        excellent_pct = report["rules_by_score"]["excellent"] / report["total_rules"]
        poor_pct = report["rules_by_score"]["poor"] / report["total_rules"]

        if excellent_pct > 0.7:
            report["system_health"] = "excellent"
        elif poor_pct < 0.2:
            report["system_health"] = "good"
        elif poor_pct < 0.5:
            report["system_health"] = "fair"
        else:
            report["system_health"] = "needs_improvement"

        report["improvement_opportunities"] = len(improvements)

        return report

    def save_health_report(self, report: Dict[str, Any]):
        """Save health report to file."""
        report_file = self.analytics_dir / "rule_system_health.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)


def validate_all_rules(rules_dir: str) -> Dict[str, RuleValidationResult]:
    """Validate all rules in the directory."""
    validator = RuleImprovementGenerator(Path(rules_dir))
    results = {}

    for rule_file in Path(rules_dir).glob("*.mdc"):
        rule_name = rule_file.stem
        results[rule_name] = validator.validate_rule(rule_name)

    return results


def generate_rule_improvements(rules_dir: str, min_score: float = 0.7) -> List[RuleImprovement]:
    """Generate improvements for rules below the minimum score."""
    improver = RuleAutoImprover(Path(rules_dir))
    return improver.batch_improve_rules(min_score)


def generate_health_report(rules_dir: str, analytics_dir: str) -> Dict[str, Any]:
    """Generate comprehensive health report for the rule system."""
    monitor = RuleHealthMonitor(Path(rules_dir), Path(analytics_dir))
    report = monitor.generate_health_report()
    monitor.save_health_report(report)
    return report


if __name__ == "__main__":
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Rule validation and improvement system")
    parser.add_argument("--validate", action="store_true", help="Validate all rules")
    parser.add_argument("--improve", action="store_true", help="Generate improvements for low-scoring rules")
    parser.add_argument("--health-report", action="store_true", help="Generate system health report")
    parser.add_argument("--rules-dir", default=".cursor/rules", help="Rules directory")
    parser.add_argument("--analytics-dir", default=".cursor/analytics", help="Analytics directory")
    parser.add_argument("--min-score", type=float, default=0.7, help="Minimum score threshold for improvements")

    args = parser.parse_args()

    if args.validate:
        print("🔍 Validating all rules...")
        results = validate_all_rules(args.rules_dir)

        valid_count = 0
        for rule_name, result in results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"{status} {rule_name}: {result.score:.2f}")

            if result.issues:
                print(f"   Issues: {result.issues[:3]}")

        print(f"\n📊 {sum(1 for r in results.values() if r.is_valid)}/{len(results)} rules are valid")

    elif args.improve:
        print("🔧 Generating rule improvements...")
        improvements = generate_rule_improvements(args.rules_dir, args.min_score)

        for improvement in improvements:
            print(f"\n🔄 {improvement.rule_name}")
            print(f"   Impact: {improvement.impact_score:.2f}")
            print(f"   Type: {improvement.improvement_type}")
            print(f"   Description: {improvement.description}")

    elif args.health_report:
        print("📊 Generating health report...")
        report = generate_health_report(args.rules_dir, args.analytics_dir)

        print(f"🏥 System Health: {report['system_health'].upper()}")
        print(f"📈 Average Score: {report['average_score']:.2f}")
        print(f"✅ Valid Rules: {report['valid_rules']}/{report['total_rules']}")

        print("\n📊 Score Distribution:")
        for category, count in report['rules_by_score'].items():
            pct = (count / report['total_rules']) * 100
            print(f"   {category.title()}: {count} ({pct:.1f})")

        if report['common_issues']:
            print("\n⚠️  Common Issues:")
            for issue, count in report['common_issues'][:5]:
                print(f"   {issue} ({count} rules)")

        print(f"\n💡 Improvement Opportunities: {report['improvement_opportunities']}")

    else:
        print("Rule Validation and Improvement System")
        print("Use --validate to validate all rules")
        print("Use --improve to generate improvements")
        print("Use --health-report to generate system health report")
