"""
Project State Analyzer for DevSynth - Part 2.

This module contains the architecture inference methods for the ProjectStateAnalyzer class.
"""

def _infer_architecture(self) -> None:
    """
    Infer the project architecture based on directory structure and file patterns.
    """
    logger.info("Inferring project architecture")
    
    # Check for common architecture patterns
    architecture_patterns = {
        'MVC': self._check_mvc_pattern(),
        'Hexagonal': self._check_hexagonal_pattern(),
        'Microservices': self._check_microservices_pattern(),
        'Layered': self._check_layered_pattern(),
        'Event-Driven': self._check_event_driven_pattern()
    }
    
    # Select the architecture with the highest confidence
    architecture, confidence = max(architecture_patterns.items(), key=lambda x: x[1])
    
    if confidence > 0.5:
        self.architecture_model = {
            'type': architecture,
            'confidence': confidence,
            'components': self._identify_components(architecture)
        }
        logger.info(f"Inferred architecture: {architecture} (confidence: {confidence:.2f})")
    else:
        self.architecture_model = {
            'type': 'Unknown',
            'confidence': 0.0,
            'components': []
        }
        logger.info("Could not confidently infer architecture")

def _check_mvc_pattern(self) -> float:
    """
    Check if the project follows the MVC pattern.
    
    Returns:
        Confidence score between 0 and 1
    """
    # Look for model, view, controller directories or files
    has_models = any('model' in path.lower() for path in self.file_index)
    has_views = any('view' in path.lower() for path in self.file_index)
    has_controllers = any('controller' in path.lower() for path in self.file_index)
    
    if has_models and has_views and has_controllers:
        return 0.9
    elif (has_models and has_views) or (has_models and has_controllers) or (has_views and has_controllers):
        return 0.6
    elif has_models or has_views or has_controllers:
        return 0.3
    else:
        return 0.0

def _check_hexagonal_pattern(self) -> float:
    """
    Check if the project follows the hexagonal (ports and adapters) pattern.
    
    Returns:
        Confidence score between 0 and 1
    """
    # Look for domain, application, adapters, ports directories
    has_domain = any('domain' in path.lower() for path in self.file_index)
    has_application = any('application' in path.lower() for path in self.file_index)
    has_adapters = any('adapter' in path.lower() for path in self.file_index)
    has_ports = any('port' in path.lower() for path in self.file_index)
    
    if has_domain and has_application and has_adapters and has_ports:
        return 0.9
    elif has_domain and (has_adapters or has_ports):
        return 0.7
    elif has_domain or has_adapters or has_ports:
        return 0.4
    else:
        return 0.0

def _check_microservices_pattern(self) -> float:
    """
    Check if the project follows a microservices pattern.
    
    Returns:
        Confidence score between 0 and 1
    """
    # Look for multiple service directories, each with its own structure
    service_dirs = [d for d in os.listdir(self.project_path) 
                   if os.path.isdir(os.path.join(self.project_path, d)) 
                   and ('service' in d.lower() or 'api' in d.lower())]
    
    # Check for Docker files, docker-compose, kubernetes configs
    has_docker = any('dockerfile' in path.lower() or 'docker-compose' in path.lower() for path in self.file_index)
    has_kubernetes = any('kubernetes' in path.lower() or 'k8s' in path.lower() for path in self.file_index)
    
    if len(service_dirs) >= 3 and (has_docker or has_kubernetes):
        return 0.9
    elif len(service_dirs) >= 2 or (len(service_dirs) >= 1 and (has_docker or has_kubernetes)):
        return 0.6
    elif len(service_dirs) >= 1 or has_docker or has_kubernetes:
        return 0.3
    else:
        return 0.0

def _check_layered_pattern(self) -> float:
    """
    Check if the project follows a layered architecture pattern.
    
    Returns:
        Confidence score between 0 and 1
    """
    # Look for common layer names
    layers = ['presentation', 'ui', 'service', 'business', 'data', 'persistence', 'repository', 'infrastructure']
    found_layers = [layer for layer in layers if any(layer in path.lower() for path in self.file_index)]
    
    if len(found_layers) >= 3:
        return 0.8
    elif len(found_layers) >= 2:
        return 0.5
    elif len(found_layers) >= 1:
        return 0.3
    else:
        return 0.0

def _check_event_driven_pattern(self) -> float:
    """
    Check if the project follows an event-driven architecture pattern.
    
    Returns:
        Confidence score between 0 and 1
    """
    # Look for event-related terms
    event_terms = ['event', 'message', 'queue', 'topic', 'subscriber', 'publisher', 'consumer', 'producer']
    found_terms = [term for term in event_terms if any(term in path.lower() for path in self.file_index)]
    
    # Check for event-driven frameworks
    event_frameworks = ['kafka', 'rabbitmq', 'activemq', 'nats', 'eventbridge', 'pubsub']
    has_frameworks = any(framework in ' '.join(self.file_index.keys()).lower() for framework in event_frameworks)
    
    if len(found_terms) >= 3 and has_frameworks:
        return 0.9
    elif len(found_terms) >= 2 or has_frameworks:
        return 0.6
    elif len(found_terms) >= 1:
        return 0.3
    else:
        return 0.0

def _identify_components(self, architecture: str) -> List[Dict[str, Any]]:
    """
    Identify components based on the inferred architecture.
    
    Args:
        architecture: The inferred architecture type
        
    Returns:
        List of component dictionaries
    """
    components = []
    
    if architecture == 'Hexagonal':
        # Identify domain entities
        domain_files = [f for f in self.code_files if 'domain' in f.lower()]
        for file in domain_files:
            components.append({
                'type': 'Domain Entity',
                'path': file,
                'name': os.path.basename(file).split('.')[0]
            })
        
        # Identify ports
        port_files = [f for f in self.code_files if 'port' in f.lower()]
        for file in port_files:
            components.append({
                'type': 'Port',
                'path': file,
                'name': os.path.basename(file).split('.')[0]
            })
        
        # Identify adapters
        adapter_files = [f for f in self.code_files if 'adapter' in f.lower()]
        for file in adapter_files:
            components.append({
                'type': 'Adapter',
                'path': file,
                'name': os.path.basename(file).split('.')[0]
            })
    
    elif architecture == 'MVC':
        # Identify models
        model_files = [f for f in self.code_files if 'model' in f.lower()]
        for file in model_files:
            components.append({
                'type': 'Model',
                'path': file,
                'name': os.path.basename(file).split('.')[0]
            })
        
        # Identify views
        view_files = [f for f in self.code_files if 'view' in f.lower()]
        for file in view_files:
            components.append({
                'type': 'View',
                'path': file,
                'name': os.path.basename(file).split('.')[0]
            })
        
        # Identify controllers
        controller_files = [f for f in self.code_files if 'controller' in f.lower()]
        for file in controller_files:
            components.append({
                'type': 'Controller',
                'path': file,
                'name': os.path.basename(file).split('.')[0]
            })
    
    # Add more architecture-specific component identification as needed
    
    return components