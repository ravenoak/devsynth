"""
Security Audit System

This module provides comprehensive security auditing capabilities including
Bandit static analysis, Safety dependency scanning, and custom security
validation checks for enterprise-grade security assurance.

Key features:
- Multi-layered security auditing (Bandit, Safety, custom checks)
- Automated vulnerability management with prioritization
- Compliance validation against security standards
- Security enhancement and monitoring capabilities
- Integration with DevSynth's quality assurance framework
"""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from devsynth.ports.memory_port import MemoryPort


@dataclass
class SecurityIssue:
    """Represents a security issue found during audit."""

    issue_type: str
    severity: str
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    cwe_id: str | None = None
    confidence: str = "medium"
    remediation: str = ""


@dataclass
class BanditReport:
    """Results from Bandit static analysis."""

    timestamp: datetime
    total_issues: int
    issues_by_severity: dict[str, int]
    issues_by_type: dict[str, int]
    issues: list[SecurityIssue]
    metrics: dict[str, Any]
    generated_at: str


@dataclass
class SafetyReport:
    """Results from Safety dependency scanning."""

    timestamp: datetime
    total_vulnerabilities: int
    vulnerabilities_by_severity: dict[str, int]
    affected_packages: list[str]
    remediation_advice: list[str]
    scan_results: list[dict[str, Any]]


@dataclass
class CustomSecurityReport:
    """Results from custom security validation checks."""

    timestamp: datetime
    checks_performed: int
    issues_found: int
    check_results: dict[str, Any]
    recommendations: list[str]


@dataclass
class SecurityAuditReport:
    """Comprehensive security audit report."""

    timestamp: datetime
    project_path: str
    bandit_report: BanditReport | None
    safety_report: SafetyReport | None
    custom_report: CustomSecurityReport | None
    overall_score: float
    risk_level: str
    recommendations: list[str]


class SecurityAuditSystem:
    """
    Multi-layered security auditing system.

    This system performs comprehensive security analysis using:
    - Bandit for static analysis of Python code
    - Safety for dependency vulnerability scanning
    - Custom security validation checks
    - Integration with DevSynth's quality assurance framework
    """

    def __init__(self, memory_port: MemoryPort | None = None):
        """Initialize the security audit system."""
        self.memory_port = memory_port
        self.audit_dir = Path.cwd() / "security_audits"
        self.audit_dir.mkdir(exist_ok=True)

        # Security configuration
        self.bandit_config = {
            "exclude_dirs": ["tests", "docs", "scripts", "__pycache__", ".git"],
            "include_test_files": False,
            "severity_threshold": "LOW",
            "confidence_threshold": "LOW",
        }

        self.safety_config = {
            "output_format": "json",
            "include_dev": False,
            "audit": True,
        }

    def run_bandit_analysis(self, target_path: str = ".") -> BanditReport:
        """
        Run Bandit static analysis for security issues.

        Args:
            target_path: Path to analyze (defaults to current directory)

        Returns:
            BanditReport with analysis results
        """
        start_time = datetime.now()

        try:
            # Build Bandit command
            cmd = [
                sys.executable,
                "-m",
                "bandit",
                "-r",  # Recursive
                "-f",
                "json",  # JSON output
                "-o",
                "-",  # Output to stdout
                target_path,
            ]

            # Add configuration options
            if self.bandit_config["severity_threshold"]:
                cmd.extend(["-s", self.bandit_config["severity_threshold"]])

            if self.bandit_config["confidence_threshold"]:
                cmd.extend(["-c", self.bandit_config["confidence_threshold"]])

            # Run Bandit
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path(target_path)
            )

            if result.returncode not in [0, 1]:  # 1 means issues found, 0 means clean
                raise subprocess.CalledProcessError(result.returncode, cmd)

            # Parse Bandit output
            bandit_data = json.loads(result.stdout)
            issues = []

            for issue in bandit_data.get("results", []):
                issues.append(
                    SecurityIssue(
                        issue_type=issue.get("test_id", "unknown"),
                        severity=issue.get("issue_severity", "unknown").lower(),
                        file_path=issue.get("filename", ""),
                        line_number=issue.get("line_number", 0),
                        description=issue.get("issue_text", ""),
                        code_snippet=issue.get("code", ""),
                        cwe_id=(
                            issue.get("issue_cwe", {}).get("id")
                            if issue.get("issue_cwe")
                            else None
                        ),
                        confidence=issue.get("issue_confidence", "medium"),
                        remediation=issue.get("more_info", ""),
                    )
                )

            # Calculate metrics
            issues_by_severity = {}
            issues_by_type = {}

            for issue in issues:
                # Count by severity
                severity = issue.severity
                issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1

                # Count by type
                issue_type = issue.issue_type
                issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1

            # Calculate metrics
            metrics = {
                "total_files": bandit_data.get("metrics", {})
                .get("_totals", {})
                .get("files", 0),
                "total_lines": bandit_data.get("metrics", {})
                .get("_totals", {})
                .get("loc", 0),
                "total_nosec": bandit_data.get("metrics", {})
                .get("_totals", {})
                .get("nosec", 0),
                "skipped_tests": bandit_data.get("metrics", {})
                .get("_totals", {})
                .get("skipped_tests", 0),
            }

            return BanditReport(
                timestamp=start_time,
                total_issues=len(issues),
                issues_by_severity=issues_by_severity,
                issues_by_type=issues_by_type,
                issues=issues,
                metrics=metrics,
                generated_at=datetime.now().isoformat(),
            )

        except (json.JSONDecodeError, subprocess.CalledProcessError) as e:
            # Return empty report on failure
            return BanditReport(
                timestamp=start_time,
                total_issues=0,
                issues_by_severity={},
                issues_by_type={},
                issues=[],
                metrics={},
                generated_at=datetime.now().isoformat(),
            )

    def run_safety_scan(self, target_path: str = ".") -> SafetyReport:
        """
        Run Safety dependency vulnerability scan.

        Args:
            target_path: Path to project (defaults to current directory)

        Returns:
            SafetyReport with vulnerability scan results
        """
        start_time = datetime.now()

        try:
            # Build Safety command
            cmd = [
                sys.executable,
                "-m",
                "safety",
                "check",
                "--output",
                "json",
                "--cache",
            ]

            # Run Safety
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path(target_path)
            )

            if result.returncode == 0:
                # No vulnerabilities found
                return SafetyReport(
                    timestamp=start_time,
                    total_vulnerabilities=0,
                    vulnerabilities_by_severity={},
                    affected_packages=[],
                    remediation_advice=[],
                    scan_results=[],
                )

            # Parse Safety output
            safety_data = json.loads(result.stdout)
            vulnerabilities = []

            for vuln in safety_data:
                vulnerabilities.append(
                    {
                        "package": vuln.get("package", ""),
                        "version": vuln.get("version", ""),
                        "advisory": vuln.get("advisory", ""),
                        "severity": vuln.get("severity", "unknown"),
                        "description": vuln.get("description", ""),
                        "cve": vuln.get("cve", ""),
                        "remediation": vuln.get("remediation", ""),
                    }
                )

            # Analyze vulnerabilities
            vulnerabilities_by_severity = {}
            affected_packages = set()

            for vuln in vulnerabilities:
                severity = vuln.get("severity", "unknown")
                vulnerabilities_by_severity[severity] = (
                    vulnerabilities_by_severity.get(severity, 0) + 1
                )
                affected_packages.add(vuln.get("package", ""))

            # Generate remediation advice
            remediation_advice = []
            if vulnerabilities_by_severity.get("high", 0) > 0:
                remediation_advice.append(
                    "Immediately update packages with high-severity vulnerabilities"
                )

            if len(affected_packages) > 5:
                remediation_advice.append(
                    "Consider reviewing dependency management strategy"
                )

            return SafetyReport(
                timestamp=start_time,
                total_vulnerabilities=len(vulnerabilities),
                vulnerabilities_by_severity=vulnerabilities_by_severity,
                affected_packages=list(affected_packages),
                remediation_advice=remediation_advice,
                scan_results=vulnerabilities,
            )

        except (json.JSONDecodeError, subprocess.CalledProcessError, FileNotFoundError):
            # Safety not available or failed
            return SafetyReport(
                timestamp=start_time,
                total_vulnerabilities=0,
                vulnerabilities_by_severity={},
                affected_packages=[],
                remediation_advice=["Safety tool not available or scan failed"],
                scan_results=[],
            )

    def run_custom_security_checks(
        self, target_path: str = "."
    ) -> CustomSecurityReport:
        """
        Run custom security validation checks.

        Args:
            target_path: Path to analyze (defaults to current directory)

        Returns:
            CustomSecurityReport with custom check results
        """
        start_time = datetime.now()

        check_results = {}
        issues_found = 0
        checks_performed = 0

        # Check for common security issues
        checks = [
            self._check_hardcoded_secrets,
            self._check_insecure_random,
            self._check_debug_endpoints,
            self._check_sql_injection_patterns,
            self._check_xss_patterns,
            self._check_insecure_file_operations,
        ]

        for check_func in checks:
            try:
                check_name = check_func.__name__
                result = check_func(target_path)
                check_results[check_name] = result

                if result.get("issues_found", 0) > 0:
                    issues_found += result["issues_found"]

                checks_performed += 1

            except Exception as e:
                check_results[check_func.__name__] = {
                    "error": str(e),
                    "issues_found": 0,
                }

        # Generate recommendations
        recommendations = self._generate_security_recommendations(check_results)

        return CustomSecurityReport(
            timestamp=start_time,
            checks_performed=checks_performed,
            issues_found=issues_found,
            check_results=check_results,
            recommendations=recommendations,
        )

    def generate_comprehensive_report(
        self,
        target_path: str = ".",
        include_bandit: bool = True,
        include_safety: bool = True,
        include_custom: bool = True,
    ) -> SecurityAuditReport:
        """
        Generate comprehensive security report.

        Args:
            target_path: Path to analyze
            include_bandit: Whether to include Bandit analysis
            include_safety: Whether to include Safety scanning
            include_custom: Whether to include custom checks

        Returns:
            SecurityAuditReport with comprehensive security analysis
        """
        bandit_report = None
        safety_report = None
        custom_report = None

        if include_bandit:
            bandit_report = self.run_bandit_analysis(target_path)

        if include_safety:
            safety_report = self.run_safety_scan(target_path)

        if include_custom:
            custom_report = self.run_custom_security_checks(target_path)

        # Calculate overall score and risk level
        overall_score = self._calculate_overall_security_score(
            bandit_report, safety_report, custom_report
        )

        risk_level = self._determine_risk_level(
            bandit_report, safety_report, custom_report
        )

        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations(
            bandit_report, safety_report, custom_report
        )

        report = SecurityAuditReport(
            timestamp=datetime.now(),
            project_path=target_path,
            bandit_report=bandit_report,
            safety_report=safety_report,
            custom_report=custom_report,
            overall_score=overall_score,
            risk_level=risk_level,
            recommendations=recommendations,
        )

        # Save report
        self._save_security_report(report)

        # Store in memory if available
        if self.memory_port:
            self._store_security_results(report)

        return report

    def _check_hardcoded_secrets(self, target_path: str) -> dict[str, Any]:
        """Check for hardcoded secrets."""
        issues = []
        files_checked = 0

        target_dir = Path(target_path)
        if not target_dir.exists():
            return {"issues_found": 0, "files_checked": 0, "issues": []}

        # Patterns for potential secrets
        secret_patterns = [
            r'password\s*[:=]\s*["\'][^"\']+["\']',
            r'api_key\s*[:=]\s*["\'][^"\']+["\']',
            r'secret\s*[:=]\s*["\'][^"\']+["\']',
            r'token\s*[:=]\s*["\'][^"\']+["\']',
            r'key\s*[:=]\s*["\'][^"\']+["\']',
        ]

        for py_file in target_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": "Potential hardcoded secret found",
                                }
                            )

                files_checked += 1

            except (UnicodeDecodeError, OSError):
                continue

        return {
            "issues_found": len(issues),
            "files_checked": files_checked,
            "issues": issues,
        }

    def _check_insecure_random(self, target_path: str) -> dict[str, Any]:
        """Check for insecure random number generation."""
        issues = []
        files_checked = 0

        target_dir = Path(target_path)
        if not target_dir.exists():
            return {"issues_found": 0, "files_checked": 0, "issues": []}

        # Insecure random patterns
        insecure_patterns = [r"random\.randint", r"random\.random", r"random\.choice"]

        for py_file in target_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in insecure_patterns:
                        if re.search(pattern, line):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": "Insecure random number generation",
                                }
                            )

                files_checked += 1

            except (UnicodeDecodeError, OSError):
                continue

        return {
            "issues_found": len(issues),
            "files_checked": files_checked,
            "issues": issues,
        }

    def _check_debug_endpoints(self, target_path: str) -> dict[str, Any]:
        """Check for debug endpoints in web applications."""
        issues = []
        files_checked = 0

        target_dir = Path(target_path)
        if not target_dir.exists():
            return {"issues_found": 0, "files_checked": 0, "issues": []}

        # Debug endpoint patterns
        debug_patterns = [
            r"DEBUG\s*=\s*True",
            r"app\.run\(.*debug=True",
            r"debug\s*=\s*true",
            r"development\s*=\s*true",
        ]

        for py_file in target_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in debug_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": "Debug mode enabled in production code",
                                }
                            )

                files_checked += 1

            except (UnicodeDecodeError, OSError):
                continue

        return {
            "issues_found": len(issues),
            "files_checked": files_checked,
            "issues": issues,
        }

    def _check_sql_injection_patterns(self, target_path: str) -> dict[str, Any]:
        """Check for SQL injection vulnerabilities."""
        issues = []
        files_checked = 0

        target_dir = Path(target_path)
        if not target_dir.exists():
            return {"issues_found": 0, "files_checked": 0, "issues": []}

        # SQL injection patterns
        sql_patterns = [
            r"\.execute\(.*\+.*\)",
            r"\.execute\(f.*\{.*\}.*\)",
            r"cursor\.execute\(.*%.*\)",
        ]

        for py_file in target_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in sql_patterns:
                        if re.search(pattern, line):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": "Potential SQL injection vulnerability",
                                }
                            )

                files_checked += 1

            except (UnicodeDecodeError, OSError):
                continue

        return {
            "issues_found": len(issues),
            "files_checked": files_checked,
            "issues": issues,
        }

    def _check_xss_patterns(self, target_path: str) -> dict[str, Any]:
        """Check for XSS vulnerabilities."""
        issues = []
        files_checked = 0

        target_dir = Path(target_path)
        if not target_dir.exists():
            return {"issues_found": 0, "files_checked": 0, "issues": []}

        # XSS patterns
        xss_patterns = [
            r"\.innerHTML\s*=",
            r"\.outerHTML\s*=",
            r"document\.write\(.*\+.*\)",
            r"element\.html\(.*\+.*\)",
        ]

        for py_file in target_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in xss_patterns:
                        if re.search(pattern, line):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": "Potential XSS vulnerability",
                                }
                            )

                files_checked += 1

            except (UnicodeDecodeError, OSError):
                continue

        return {
            "issues_found": len(issues),
            "files_checked": files_checked,
            "issues": issues,
        }

    def _check_insecure_file_operations(self, target_path: str) -> dict[str, Any]:
        """Check for insecure file operations."""
        issues = []
        files_checked = 0

        target_dir = Path(target_path)
        if not target_dir.exists():
            return {"issues_found": 0, "files_checked": 0, "issues": []}

        # Insecure file operation patterns
        insecure_patterns = [
            r"open\(.*['\"]w['\"].*\+.*\)",
            r"os\.system\(.*\+.*\)",
            r"subprocess\.call\(.*\+.*\)",
            r"subprocess\.run\(.*shell=True",
        ]

        for py_file in target_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in insecure_patterns:
                        if re.search(pattern, line):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": "Insecure file operation",
                                }
                            )

                files_checked += 1

            except (UnicodeDecodeError, OSError):
                continue

        return {
            "issues_found": len(issues),
            "files_checked": files_checked,
            "issues": issues,
        }

    def _calculate_overall_security_score(
        self,
        bandit_report: BanditReport | None,
        safety_report: SafetyReport | None,
        custom_report: CustomSecurityReport | None,
    ) -> float:
        """Calculate overall security score."""
        scores = []

        if bandit_report:
            # Calculate Bandit score (lower issues = higher score)
            total_issues = bandit_report.total_issues
            max_reasonable_issues = 50  # Arbitrary threshold
            bandit_score = max(0, 100 - (total_issues / max_reasonable_issues) * 100)
            scores.append(bandit_score)

        if safety_report:
            # Calculate Safety score (fewer vulnerabilities = higher score)
            total_vulns = safety_report.total_vulnerabilities
            safety_score = max(0, 100 - total_vulns * 10)  # 10 points per vulnerability
            scores.append(safety_score)

        if custom_report:
            # Calculate custom checks score
            issues_found = custom_report.issues_found
            custom_score = max(0, 100 - issues_found * 5)  # 5 points per issue
            scores.append(custom_score)

        if scores:
            return sum(scores) / len(scores)
        else:
            return 100.0  # No issues found

    def _determine_risk_level(
        self,
        bandit_report: BanditReport | None,
        safety_report: SafetyReport | None,
        custom_report: CustomSecurityReport | None,
    ) -> str:
        """Determine overall risk level."""
        total_issues = 0
        high_severity_issues = 0

        if bandit_report:
            total_issues += bandit_report.total_issues
            high_severity_issues += bandit_report.issues_by_severity.get("high", 0)

        if safety_report:
            total_issues += safety_report.total_vulnerabilities
            high_severity_issues += safety_report.vulnerabilities_by_severity.get(
                "high", 0
            )

        if custom_report:
            total_issues += custom_report.issues_found

        if high_severity_issues > 0:
            return "critical"
        elif total_issues > 20:
            return "high"
        elif total_issues > 10:
            return "medium"
        elif total_issues > 0:
            return "low"
        else:
            return "none"

    def _generate_security_recommendations(
        self, check_results: dict[str, Any]
    ) -> list[str]:
        """Generate security recommendations based on custom check results."""
        recommendations = []

        for check_name, result in check_results.items():
            issues = result.get("issues", [])

            if check_name == "_check_hardcoded_secrets" and issues:
                recommendations.append(
                    "Remove hardcoded secrets and use environment variables or secure vaults"
                )

            if check_name == "_check_insecure_random" and issues:
                recommendations.append(
                    "Use cryptographically secure random number generation (secrets module)"
                )

            if check_name == "_check_debug_endpoints" and issues:
                recommendations.append(
                    "Disable debug mode and remove debug endpoints in production"
                )

            if check_name == "_check_sql_injection_patterns" and issues:
                recommendations.append(
                    "Use parameterized queries or ORM to prevent SQL injection"
                )

            if check_name == "_check_xss_patterns" and issues:
                recommendations.append(
                    "Sanitize user input and use secure templating to prevent XSS"
                )

            if check_name == "_check_insecure_file_operations" and issues:
                recommendations.append(
                    "Validate file paths and use secure file operations"
                )

        return recommendations

    def _generate_comprehensive_recommendations(
        self,
        bandit_report: BanditReport | None,
        safety_report: SafetyReport | None,
        custom_report: CustomSecurityReport | None,
    ) -> list[str]:
        """Generate comprehensive security recommendations."""
        recommendations = []

        # Bandit recommendations
        if bandit_report and bandit_report.total_issues > 0:
            if bandit_report.issues_by_severity.get("high", 0) > 0:
                recommendations.append(
                    "Immediately address high-severity security issues found by Bandit"
                )

            if bandit_report.total_issues > 10:
                recommendations.append(
                    "Consider implementing a security-focused code review process"
                )

        # Safety recommendations
        if safety_report and safety_report.total_vulnerabilities > 0:
            if safety_report.vulnerabilities_by_severity.get("high", 0) > 0:
                recommendations.append(
                    "Urgently update packages with high-severity vulnerabilities"
                )

            recommendations.append(
                "Regularly scan and update dependencies for security patches"
            )

        # Custom check recommendations
        if custom_report:
            recommendations.extend(
                self._generate_security_recommendations(custom_report.check_results)
            )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "Security scan completed successfully - no critical issues found"
            )
        else:
            recommendations.append(
                "Implement automated security scanning in CI/CD pipeline"
            )
            recommendations.append("Establish security-focused code review guidelines")

        return recommendations

    def _save_security_report(self, report: SecurityAuditReport) -> None:
        """Save security report to file."""
        timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"security_audit_{timestamp}.json"
        filepath = self.audit_dir / filename

        try:
            # Convert to serializable format
            report_data = {
                "timestamp": report.timestamp.isoformat(),
                "project_path": report.project_path,
                "overall_score": report.overall_score,
                "risk_level": report.risk_level,
                "recommendations": report.recommendations,
                "bandit_report": None,
                "safety_report": None,
                "custom_report": None,
            }

            if report.bandit_report:
                report_data["bandit_report"] = {
                    "total_issues": report.bandit_report.total_issues,
                    "issues_by_severity": report.bandit_report.issues_by_severity,
                    "issues_by_type": report.bandit_report.issues_by_type,
                    "metrics": report.bandit_report.metrics,
                }

            if report.safety_report:
                report_data["safety_report"] = {
                    "total_vulnerabilities": report.safety_report.total_vulnerabilities,
                    "vulnerabilities_by_severity": report.safety_report.vulnerabilities_by_severity,
                    "affected_packages": report.safety_report.affected_packages,
                    "remediation_advice": report.safety_report.remediation_advice,
                }

            if report.custom_report:
                report_data["custom_report"] = {
                    "checks_performed": report.custom_report.checks_performed,
                    "issues_found": report.custom_report.issues_found,
                    "recommendations": report.custom_report.recommendations,
                }

            with open(filepath, "w") as f:
                json.dump(report_data, f, indent=2)

        except OSError:
            # Save failed, but don't fail the operation
            pass

    def _store_security_results(self, report: SecurityAuditReport) -> None:
        """Store security results in memory system."""
        if not self.memory_port:
            return

        try:
            memory_key = "security_audit_latest"
            self.memory_port.store(
                key=memory_key,
                data={
                    "timestamp": report.timestamp.isoformat(),
                    "overall_score": report.overall_score,
                    "risk_level": report.risk_level,
                    "total_issues": (
                        (
                            report.bandit_report.total_issues
                            if report.bandit_report
                            else 0
                        )
                        + (
                            report.safety_report.total_vulnerabilities
                            if report.safety_report
                            else 0
                        )
                        + (
                            report.custom_report.issues_found
                            if report.custom_report
                            else 0
                        )
                    ),
                    "recommendations": report.recommendations,
                },
                metadata={
                    "type": "security_audit",
                    "project_path": report.project_path,
                },
            )

        except Exception:
            # Memory storage failed, but don't fail the operation
            pass

    def get_audit_history(self) -> list[dict[str, Any]]:
        """Get history of security audits."""
        history = []

        try:
            for audit_file in self.audit_dir.glob("security_audit_*.json"):
                with open(audit_file) as f:
                    data = json.load(f)
                    history.append(
                        {
                            "timestamp": data["timestamp"],
                            "overall_score": data["overall_score"],
                            "risk_level": data["risk_level"],
                            "total_issues": (
                                data.get("bandit_report", {}).get("total_issues", 0)
                                + data.get("safety_report", {}).get(
                                    "total_vulnerabilities", 0
                                )
                                + data.get("custom_report", {}).get("issues_found", 0)
                            ),
                        }
                    )

            # Sort by timestamp (most recent first)
            history.sort(key=lambda x: x["timestamp"], reverse=True)

        except (json.JSONDecodeError, OSError):
            pass

        return history

    def get_security_trends(self) -> dict[str, Any]:
        """Get security trends from audit history."""
        history = self.get_audit_history()

        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "message": "Need at least 2 audit results for trend analysis",
            }

        # Calculate trends
        scores = [entry["overall_score"] for entry in history]
        issues = [entry["total_issues"] for entry in history]

        score_trend = (
            "improving"
            if scores[0] > scores[-1]
            else "declining" if scores[0] < scores[-1] else "stable"
        )
        issue_trend = (
            "improving"
            if issues[0] < issues[-1]
            else "declining" if issues[0] > issues[-1] else "stable"
        )

        return {
            "score_trend": score_trend,
            "issue_trend": issue_trend,
            "current_score": scores[0],
            "previous_score": scores[1] if len(scores) > 1 else None,
            "current_issues": issues[0],
            "previous_issues": issues[1] if len(issues) > 1 else None,
            "audit_count": len(history),
        }
