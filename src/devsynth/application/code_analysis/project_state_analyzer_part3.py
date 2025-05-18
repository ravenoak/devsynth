"""
Project State Analyzer for DevSynth - Part 3.

This module contains the requirements-specification alignment and specification-code alignment
analysis methods for the ProjectStateAnalyzer class.
"""

def _analyze_requirements_spec_alignment(self) -> Dict[str, Any]:
    """
    Analyze alignment between requirements and specifications.
    
    Returns:
        Dictionary with alignment analysis results
    """
    logger.info("Analyzing requirements-specification alignment")
    
    alignment_results = {
        'total_requirements': 0,
        'total_specifications': 0,
        'matched_requirements': 0,
        'unmatched_requirements': [],
        'unmatched_specifications': [],
        'alignment_score': 0.0
    }
    
    # Skip if no requirements or specifications
    if not self.requirements_files or not self.specification_files:
        logger.info("Skipping requirements-specification alignment: missing files")
        return alignment_results
    
    # Extract requirements
    requirements = self._extract_requirements()
    alignment_results['total_requirements'] = len(requirements)
    
    # Extract specifications
    specifications = self._extract_specifications()
    alignment_results['total_specifications'] = len(specifications)
    
    # Match requirements to specifications
    matched_reqs = []
    for req in requirements:
        matched = False
        for spec in specifications:
            if self._is_requirement_matched_by_spec(req, spec):
                matched = True
                break
        
        if matched:
            matched_reqs.append(req)
        else:
            alignment_results['unmatched_requirements'].append(req)
    
    alignment_results['matched_requirements'] = len(matched_reqs)
    
    # Find specifications without matching requirements
    for spec in specifications:
        matched = False
        for req in requirements:
            if self._is_requirement_matched_by_spec(req, spec):
                matched = True
                break
        
        if not matched:
            alignment_results['unmatched_specifications'].append(spec)
    
    # Calculate alignment score
    if alignment_results['total_requirements'] > 0:
        alignment_results['alignment_score'] = alignment_results['matched_requirements'] / alignment_results['total_requirements']
    
    logger.info(f"Requirements-specification alignment score: {alignment_results['alignment_score']:.2f}")
    return alignment_results

def _extract_requirements(self) -> List[Dict[str, Any]]:
    """
    Extract requirements from requirements files.
    
    Returns:
        List of requirement dictionaries
    """
    requirements = []
    
    for req_file in self.requirements_files:
        try:
            with open(os.path.join(self.project_path, req_file), 'r') as f:
                content = f.read()
            
            # Simple extraction of requirements (can be enhanced with NLP)
            # Look for bullet points, numbered lists, or sections
            lines = content.split('\n')
            current_section = "General"
            
            for line in lines:
                line = line.strip()
                
                # Check for section headers
                if line.startswith('# '):
                    current_section = line[2:].strip()
                    continue
                elif line.startswith('## '):
                    current_section = line[3:].strip()
                    continue
                
                # Check for requirement patterns
                req_pattern = re.match(r'^[-*]|\d+\.\s+(.+)$', line)
                if req_pattern:
                    req_text = req_pattern.group(1).strip()
                    if req_text:
                        requirements.append({
                            'text': req_text,
                            'section': current_section,
                            'source_file': req_file
                        })
        except Exception as e:
            logger.error(f"Error extracting requirements from {req_file}: {str(e)}")
    
    return requirements

def _extract_specifications(self) -> List[Dict[str, Any]]:
    """
    Extract specifications from specification files.
    
    Returns:
        List of specification dictionaries
    """
    specifications = []
    
    for spec_file in self.specification_files:
        try:
            with open(os.path.join(self.project_path, spec_file), 'r') as f:
                content = f.read()
            
            # Simple extraction of specifications (can be enhanced with NLP)
            # Look for bullet points, numbered lists, or sections
            lines = content.split('\n')
            current_section = "General"
            
            for line in lines:
                line = line.strip()
                
                # Check for section headers
                if line.startswith('# '):
                    current_section = line[2:].strip()
                    continue
                elif line.startswith('## '):
                    current_section = line[3:].strip()
                    continue
                
                # Check for specification patterns
                spec_pattern = re.match(r'^[-*]|\d+\.\s+(.+)$', line)
                if spec_pattern:
                    spec_text = spec_pattern.group(1).strip()
                    if spec_text:
                        specifications.append({
                            'text': spec_text,
                            'section': current_section,
                            'source_file': spec_file
                        })
        except Exception as e:
            logger.error(f"Error extracting specifications from {spec_file}: {str(e)}")
    
    return specifications

def _is_requirement_matched_by_spec(self, requirement: Dict[str, Any], specification: Dict[str, Any]) -> bool:
    """
    Check if a requirement is matched by a specification.
    
    Args:
        requirement: Requirement dictionary
        specification: Specification dictionary
        
    Returns:
        True if the requirement is matched by the specification
    """
    # Simple matching based on text similarity (can be enhanced with NLP)
    req_text = requirement['text'].lower()
    spec_text = specification['text'].lower()
    
    # Check for direct keyword matches
    req_keywords = set(re.findall(r'\b\w+\b', req_text))
    spec_keywords = set(re.findall(r'\b\w+\b', spec_text))
    
    # Calculate keyword overlap
    if len(req_keywords) > 0:
        overlap = len(req_keywords.intersection(spec_keywords)) / len(req_keywords)
        return overlap > 0.5
    
    return False

def _analyze_spec_code_alignment(self) -> Dict[str, Any]:
    """
    Analyze alignment between specifications and code.
    
    Returns:
        Dictionary with alignment analysis results
    """
    logger.info("Analyzing specification-code alignment")
    
    alignment_results = {
        'total_specifications': 0,
        'implemented_specifications': 0,
        'unimplemented_specifications': [],
        'implementation_score': 0.0
    }
    
    # Skip if no specifications
    if not self.specification_files:
        logger.info("Skipping specification-code alignment: no specification files")
        return alignment_results
    
    # Extract specifications
    specifications = self._extract_specifications()
    alignment_results['total_specifications'] = len(specifications)
    
    # For each specification, check if it's implemented in code
    implemented_specs = []
    for spec in specifications:
        if self._is_specification_implemented(spec):
            implemented_specs.append(spec)
        else:
            alignment_results['unimplemented_specifications'].append(spec)
    
    alignment_results['implemented_specifications'] = len(implemented_specs)
    
    # Calculate implementation score
    if alignment_results['total_specifications'] > 0:
        alignment_results['implementation_score'] = alignment_results['implemented_specifications'] / alignment_results['total_specifications']
    
    logger.info(f"Specification-code implementation score: {alignment_results['implementation_score']:.2f}")
    return alignment_results

def _is_specification_implemented(self, specification: Dict[str, Any]) -> bool:
    """
    Check if a specification is implemented in code.
    
    Args:
        specification: Specification dictionary
        
    Returns:
        True if the specification is implemented
    """
    # Simple implementation check based on keyword matching (can be enhanced with AST parsing)
    spec_text = specification['text'].lower()
    
    # Extract key terms from the specification
    key_terms = set(re.findall(r'\b\w+\b', spec_text))
    key_terms = {term for term in key_terms if len(term) > 3}  # Filter out short words
    
    # Check if key terms appear in code files
    for code_file in self.code_files:
        try:
            with open(os.path.join(self.project_path, code_file), 'r') as f:
                content = f.read().lower()
            
            # Count how many key terms appear in the code
            found_terms = sum(1 for term in key_terms if term in content)
            
            # If more than half of the key terms are found, consider it implemented
            if found_terms > len(key_terms) / 2:
                return True
        except Exception as e:
            logger.error(f"Error checking implementation in {code_file}: {str(e)}")
    
    return False