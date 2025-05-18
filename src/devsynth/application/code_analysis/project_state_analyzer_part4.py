"""
Project State Analyzer for DevSynth - Part 4.

This module contains the health report generation methods for the ProjectStateAnalyzer class.
"""

def _generate_health_report(self, req_spec_alignment: Dict[str, Any], spec_code_alignment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a project health report.
    
    Args:
        req_spec_alignment: Requirements-specification alignment results
        spec_code_alignment: Specification-code alignment results
        
    Returns:
        Dictionary containing the health report
    """
    logger.info("Generating project health report")
    
    # Calculate overall health score
    health_score = 0.0
    factors = 0
    
    if req_spec_alignment['total_requirements'] > 0:
        health_score += req_spec_alignment['alignment_score']
        factors += 1
    
    if spec_code_alignment['total_specifications'] > 0:
        health_score += spec_code_alignment['implementation_score']
        factors += 1
    
    if factors > 0:
        health_score /= factors
    
    # Generate report
    report = {
        'project_path': self.project_path,
        'file_count': len(self.file_index),
        'languages': list(self.detected_languages),
        'architecture': self.architecture_model,
        'requirements_count': len(self.requirements_files),
        'specifications_count': len(self.specification_files),
        'test_count': len(self.test_files),
        'code_count': len(self.code_files),
        'requirements_spec_alignment': req_spec_alignment,
        'spec_code_alignment': spec_code_alignment,
        'health_score': health_score,
        'issues': self._identify_issues(req_spec_alignment, spec_code_alignment),
        'recommendations': self._generate_recommendations(req_spec_alignment, spec_code_alignment)
    }
    
    logger.info(f"Project health score: {health_score:.2f}")
    return report

def _identify_issues(self, req_spec_alignment: Dict[str, Any], spec_code_alignment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify issues in the project.
    
    Args:
        req_spec_alignment: Requirements-specification alignment results
        spec_code_alignment: Specification-code alignment results
        
    Returns:
        List of issue dictionaries
    """
    issues = []
    
    # Check for missing requirements files
    if not self.requirements_files:
        issues.append({
            'severity': 'high',
            'type': 'missing_requirements',
            'description': 'No requirements files found in the project'
        })
    
    # Check for missing specification files
    if not self.specification_files:
        issues.append({
            'severity': 'high',
            'type': 'missing_specifications',
            'description': 'No specification files found in the project'
        })
    
    # Check for missing test files
    if not self.test_files:
        issues.append({
            'severity': 'medium',
            'type': 'missing_tests',
            'description': 'No test files found in the project'
        })
    
    # Check for unmatched requirements
    if req_spec_alignment['unmatched_requirements']:
        issues.append({
            'severity': 'high',
            'type': 'unmatched_requirements',
            'description': f"{len(req_spec_alignment['unmatched_requirements'])} requirements not matched by specifications",
            'details': req_spec_alignment['unmatched_requirements']
        })
    
    # Check for unimplemented specifications
    if spec_code_alignment['unimplemented_specifications']:
        issues.append({
            'severity': 'medium',
            'type': 'unimplemented_specifications',
            'description': f"{len(spec_code_alignment['unimplemented_specifications'])} specifications not implemented in code",
            'details': spec_code_alignment['unimplemented_specifications']
        })
    
    return issues

def _generate_recommendations(self, req_spec_alignment: Dict[str, Any], spec_code_alignment: Dict[str, Any]) -> List[str]:
    """
    Generate recommendations based on the analysis.
    
    Args:
        req_spec_alignment: Requirements-specification alignment results
        spec_code_alignment: Specification-code alignment results
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Recommendations for missing files
    if not self.requirements_files:
        recommendations.append("Create requirements documentation to clearly define project goals")
    
    if not self.specification_files:
        recommendations.append("Develop specifications based on requirements to guide implementation")
    
    if not self.test_files:
        recommendations.append("Add tests to ensure code quality and prevent regressions")
    
    # Recommendations for alignment issues
    if req_spec_alignment['unmatched_requirements']:
        recommendations.append(f"Update specifications to address {len(req_spec_alignment['unmatched_requirements'])} unmatched requirements")
    
    if spec_code_alignment['unimplemented_specifications']:
        recommendations.append(f"Implement code for {len(spec_code_alignment['unimplemented_specifications'])} unimplemented specifications")
    
    # Architecture recommendations
    if self.architecture_model and self.architecture_model['type'] != 'Unknown':
        if self.architecture_model['confidence'] < 0.7:
            recommendations.append(f"Consider clarifying the {self.architecture_model['type']} architecture by reorganizing files and directories")
    else:
        recommendations.append("Consider adopting a clear architectural pattern to improve code organization")
    
    # Language recommendations
    if len(self.detected_languages) > 3:
        recommendations.append("Consider consolidating the number of programming languages used in the project")
    
    # Test recommendations
    if len(self.test_files) < len(self.code_files) * 0.5:
        recommendations.append("Increase test coverage to improve code quality and maintainability")
    
    return recommendations