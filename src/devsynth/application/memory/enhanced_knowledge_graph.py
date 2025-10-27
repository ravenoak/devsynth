"""
Enhanced Knowledge Graph with Business Intent Layer

This module provides the enhanced knowledge graph implementation with business
intent discovery, semantic linking, and multi-hop reasoning capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from ...domain.models.memory import MemeticUnit
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class Entity:
    """Enhanced entity in the knowledge graph with business context."""
    id: str
    type: str
    properties: Dict[str, Any]
    source_file: str = ""
    business_context: Dict[str, Any] = field(default_factory=dict)
    intent_links: List[str] = field(default_factory=list)
    semantic_vectors: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "source_file": self.source_file,
            "business_context": self.business_context,
            "intent_links": self.intent_links,
            "semantic_vectors": self.semantic_vectors
        }


@dataclass
class Relationship:
    """Enhanced relationship with semantic strength and validation."""
    source_id: str
    target_id: str
    type: str
    strength: float
    evidence: str = ""
    validation_method: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary for serialization."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "strength": self.strength,
            "evidence": self.evidence,
            "validation_method": self.validation_method,
            "metadata": self.metadata
        }


@dataclass
class IntentLink:
    """Represents a link between code and business intent."""
    entity_id: str
    requirement_id: str
    intent_type: str  # "IMPLEMENTS", "SATISFIES", "VALIDATES", etc.
    confidence: float
    evidence: str
    semantic_similarity: float = 0.0
    validation_method: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert intent link to dictionary."""
        return {
            "entity_id": self.entity_id,
            "requirement_id": self.requirement_id,
            "intent_type": self.intent_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "semantic_similarity": self.semantic_similarity,
            "validation_method": self.validation_method
        }


class EnhancedKnowledgeGraph:
    """Enhanced knowledge graph with business intent and semantic linking."""

    def __init__(self):
        """Initialize the enhanced knowledge graph."""
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.intent_links: Dict[str, IntentLink] = {}

        # Indexes for efficient querying
        self._type_index: Dict[str, Set[str]] = {}
        self._property_index: Dict[str, Dict[str, Set[str]]] = {}

        # Intent discovery components
        self.intent_discovery_engine = IntentDiscoveryEngine()

        logger.info("Enhanced knowledge graph initialized")

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the knowledge graph."""
        self.entities[entity.id] = entity

        # Update indexes
        self._update_type_index(entity)
        self._update_property_index(entity)

        logger.debug(f"Added entity {entity.id} of type {entity.type}")

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between entities."""
        rel_id = f"{relationship.source_id}--{relationship.type}-->{relationship.target_id}"
        self.relationships[rel_id] = relationship

        logger.debug(f"Added relationship {rel_id} with strength {relationship.strength}")

    def add_intent_link(self, intent_link: IntentLink) -> None:
        """Add an intent link between code and business requirements."""
        link_id = f"{intent_link.entity_id}--{intent_link.intent_type}-->{intent_link.requirement_id}"
        self.intent_links[link_id] = intent_link

        # Update entity intent links
        if intent_link.entity_id in self.entities:
            self.entities[intent_link.entity_id].intent_links.append(link_id)

        logger.debug(f"Added intent link {link_id} with confidence {intent_link.confidence}")

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        entity_ids = self._type_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids if eid in self.entities]

    def get_connected_entities(self, entity_id: str, relationship_type: str = None) -> List[Entity]:
        """Get entities connected to the given entity."""
        connected = []

        # Find relationships involving this entity
        for rel_id, relationship in self.relationships.items():
            if (relationship.source_id == entity_id or
                relationship.target_id == entity_id):

                if relationship_type and relationship.type != relationship_type:
                    continue

                # Get the connected entity
                connected_id = (relationship.target_id if relationship.source_id == entity_id
                              else relationship.source_id)

                if connected_id in self.entities:
                    connected.append(self.entities[connected_id])

        return connected

    def query_business_context(self, query: str) -> List[Entity]:
        """Query entities related to business context."""
        # This is a simplified implementation
        # In practice, would use semantic search and multi-hop traversal

        business_types = ["BusinessRequirement", "DesignDecision", "UserJourney"]
        business_entities = []

        for entity_type in business_types:
            entities = self.get_entities_by_type(entity_type)
            business_entities.extend(entities)

        # Filter by relevance to query (simplified)
        relevant_entities = []
        query_lower = query.lower()

        for entity in business_entities:
            # Check if query terms appear in entity properties
            for prop_value in entity.properties.values():
                if isinstance(prop_value, str) and query_lower in prop_value.lower():
                    relevant_entities.append(entity)
                    break

        return relevant_entities

    def find_semantic_matches(self, target_entity: Entity, max_results: int = 10) -> List[Entity]:
        """Find entities semantically similar to the target."""
        # Simplified semantic matching based on keywords and properties
        matches = []

        target_keywords = set()
        for prop_value in target_entity.properties.values():
            if isinstance(prop_value, str):
                target_keywords.update(prop_value.lower().split())

        # Score other entities by keyword overlap
        scored_entities = []
        for entity in self.entities.values():
            if entity.id == target_entity.id:
                continue

            entity_keywords = set()
            for prop_value in entity.properties.values():
                if isinstance(prop_value, str):
                    entity_keywords.update(prop_value.lower().split())

            # Calculate overlap score
            overlap = len(target_keywords.intersection(entity_keywords))
            if overlap > 0:
                score = overlap / len(target_keywords.union(entity_keywords))
                scored_entities.append((entity, score))

        # Sort by score and return top matches
        scored_entities.sort(key=lambda x: x[1], reverse=True)
        return [entity for entity, _ in scored_entities[:max_results]]

    def _update_type_index(self, entity: Entity) -> None:
        """Update type index for efficient querying."""
        if entity.type not in self._type_index:
            self._type_index[entity.type] = set()
        self._type_index[entity.type].add(entity.id)

    def _update_property_index(self, entity: Entity) -> None:
        """Update property index for efficient querying."""
        for prop_name, prop_value in entity.properties.items():
            if prop_name not in self._property_index:
                self._property_index[prop_name] = {}

            prop_str = str(prop_value)
            if prop_str not in self._property_index[prop_name]:
                self._property_index[prop_name][prop_str] = set()

            self._property_index[prop_name][prop_str].add(entity.id)

    def discover_intent_relationships(self) -> List[IntentLink]:
        """Discover intent relationships between code and business entities."""
        intent_links = []

        # Get business requirements
        requirements = self.get_entities_by_type("BusinessRequirement")

        # Get code entities (functions, classes, etc.)
        code_entities = []
        for entity_type in ["Function", "Class", "Module"]:
            code_entities.extend(self.get_entities_by_type(entity_type))

        # Find intent links between requirements and code
        for requirement in requirements:
            for code_entity in code_entities:
                intent_link = self.intent_discovery_engine.discover_intent(
                    code_entity, requirement
                )
                if intent_link and intent_link.confidence > 0.6:  # Confidence threshold
                    intent_links.append(intent_link)
                    self.add_intent_link(intent_link)

        logger.info(f"Discovered {len(intent_links)} intent relationships")
        return intent_links

    def calculate_blast_radius(self, start_entity_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """Calculate the blast radius of changes to an entity."""
        visited = set([start_entity_id])
        current_level = [start_entity_id]
        all_affected = set([start_entity_id])

        # Multi-hop traversal to find all affected entities
        for depth in range(max_depth):
            next_level = []

            for entity_id in current_level:
                # Find all connected entities
                connected = self.get_connected_entities(entity_id)

                for connected_entity in connected:
                    if connected_entity.id not in visited:
                        visited.add(connected_entity.id)
                        next_level.append(connected_entity.id)
                        all_affected.add(connected_entity.id)

            if not next_level:
                break  # No more connections

            current_level = next_level

        # Calculate impact metrics
        impact_metrics = self._calculate_impact_metrics(all_affected, start_entity_id)

        return {
            "start_entity": start_entity_id,
            "affected_entities": list(all_affected),
            "blast_radius": len(all_affected) - 1,  # Exclude starting entity
            "max_depth": len(visited) if visited else 0,
            "impact_metrics": impact_metrics,
            "traversal_path": list(visited)
        }

    def _calculate_impact_metrics(self, affected_entities: Set[str], start_entity_id: str) -> Dict[str, Any]:
        """Calculate impact metrics for the blast radius analysis."""
        if not affected_entities:
            return {}

        # Count affected entity types
        type_counts = {}
        business_impact = 0

        for entity_id in affected_entities:
            if entity_id in self.entities:
                entity = self.entities[entity_id]
                entity_type = entity.type

                type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

                # Calculate business impact
                if entity_type == "BusinessRequirement":
                    business_impact += 3  # High impact
                elif entity_type in ["UserJourney", "DesignDecision"]:
                    business_impact += 2  # Medium impact
                elif entity_type in ["Function", "Class"]:
                    business_impact += 1  # Lower impact

        return {
            "affected_types": type_counts,
            "business_impact_score": business_impact,
            "total_entities_affected": len(affected_entities),
            "risk_level": self._assess_risk_level(business_impact, len(affected_entities))
        }

    def _assess_risk_level(self, business_impact: int, entity_count: int) -> str:
        """Assess risk level based on impact metrics."""
        if business_impact >= 10 or entity_count >= 20:
            return "high"
        elif business_impact >= 5 or entity_count >= 10:
            return "medium"
        else:
            return "low"

    def validate_intent_links(self) -> Dict[str, Any]:
        """Validate intent links for consistency and accuracy."""
        validation_results = {
            "total_links": len(self.intent_links),
            "valid_links": 0,
            "invalid_links": 0,
            "low_confidence_links": 0,
            "validation_errors": []
        }

        for link_id, intent_link in self.intent_links.items():
            is_valid = True
            errors = []

            # Check if linked entities exist
            if intent_link.entity_id not in self.entities:
                is_valid = False
                errors.append(f"Entity {intent_link.entity_id} not found")

            if intent_link.requirement_id not in self.entities:
                is_valid = False
                errors.append(f"Requirement {intent_link.requirement_id} not found")

            # Check confidence threshold
            if intent_link.confidence < 0.6:
                validation_results["low_confidence_links"] += 1

            if is_valid:
                validation_results["valid_links"] += 1
            else:
                validation_results["invalid_links"] += 1
                validation_results["validation_errors"].extend(errors)

        logger.info(f"Validated {len(self.intent_links)} intent links: {validation_results['valid_links']} valid, {validation_results['invalid_links']} invalid")
        return validation_results

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire graph to dictionary for serialization."""
        return {
            "entities": {eid: entity.to_dict() for eid, entity in self.entities.items()},
            "relationships": {rid: rel.to_dict() for rid, rel in self.relationships.items()},
            "intent_links": {lid: link.to_dict() for lid, link in self.intent_links.items()},
            "metadata": {
                "entity_count": len(self.entities),
                "relationship_count": len(self.relationships),
                "intent_link_count": len(self.intent_links),
                "entity_types": list(self._type_index.keys()),
                "created_at": self._get_timestamp()
            }
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()


class IntentDiscoveryEngine:
    """Engine for discovering intent relationships between code and business requirements."""

    def __init__(self, similarity_threshold: float = 0.7):
        """Initialize the intent discovery engine."""
        self.similarity_threshold = similarity_threshold
        logger.info(f"Intent discovery engine initialized with threshold {similarity_threshold}")

    def discover_intent(self, code_entity: Entity, requirement: Entity) -> Optional[IntentLink]:
        """Discover intent relationship between code and requirement."""
        # Calculate semantic similarity between code and requirement
        similarity = self._calculate_semantic_similarity(code_entity, requirement)

        if similarity < self.similarity_threshold:
            return None

        # Analyze naming patterns
        naming_confidence = self._analyze_naming_patterns(code_entity, requirement)

        # Analyze comment content
        comment_confidence = self._analyze_comment_content(code_entity, requirement)

        # Analyze implementation patterns
        implementation_confidence = self._analyze_implementation_patterns(code_entity, requirement)

        # Combine confidence scores
        overall_confidence = (similarity * 0.4 +
                            naming_confidence * 0.3 +
                            comment_confidence * 0.2 +
                            implementation_confidence * 0.1)

        if overall_confidence < self.similarity_threshold:
            return None

        # Generate evidence
        evidence_parts = []
        if similarity > 0.8:
            evidence_parts.append(f"High semantic similarity ({similarity:.2f})")
        if naming_confidence > 0.7:
            evidence_parts.append("Strong naming pattern match")
        if comment_confidence > 0.7:
            evidence_parts.append("Comment content alignment")
        if implementation_confidence > 0.7:
            evidence_parts.append("Implementation pattern match")

        evidence = "; ".join(evidence_parts) if evidence_parts else f"Semantic similarity: {similarity:.2f}"

        # Determine intent type
        intent_type = self._determine_intent_type(code_entity, requirement, overall_confidence)

        return IntentLink(
            entity_id=code_entity.id,
            requirement_id=requirement.id,
            intent_type=intent_type,
            confidence=overall_confidence,
            evidence=evidence,
            semantic_similarity=similarity,
            validation_method="semantic_similarity_and_pattern_analysis"
        )

    def _calculate_semantic_similarity(self, code_entity: Entity, requirement: Entity) -> float:
        """Calculate semantic similarity between code entity and requirement."""
        # Simplified semantic similarity based on text overlap
        code_text = " ".join(str(v) for v in code_entity.properties.values()).lower()
        requirement_text = " ".join(str(v) for v in requirement.properties.values()).lower()

        # Extract meaningful words
        def extract_keywords(text: str) -> Set[str]:
            words = text.split()
            # Filter for meaningful words (length > 2, not common stop words)
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            return {word for word in words if len(word) > 2 and word not in stop_words}

        code_keywords = extract_keywords(code_text)
        requirement_keywords = extract_keywords(requirement_text)

        if not code_keywords or not requirement_keywords:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(code_keywords.intersection(requirement_keywords))
        union = len(code_keywords.union(requirement_keywords))

        return intersection / union if union > 0 else 0.0

    def _analyze_naming_patterns(self, code_entity: Entity, requirement: Entity) -> float:
        """Analyze naming patterns for intent alignment."""
        code_name = code_entity.properties.get("name", "").lower()
        requirement_desc = requirement.properties.get("description", "").lower()

        # Check for business domain keywords in code names
        business_indicators = [
            "user", "auth", "payment", "admin", "report", "config",
            "profile", "dashboard", "notification", "search", "filter"
        ]

        name_matches = 0
        for indicator in business_indicators:
            if indicator in code_name or indicator in requirement_desc:
                name_matches += 1

        # Normalize by number of indicators checked
        return name_matches / len(business_indicators)

    def _analyze_comment_content(self, code_entity: Entity, requirement: Entity) -> float:
        """Analyze comment content for business intent."""
        # Look for business context in entity properties
        code_props = code_entity.properties
        requirement_props = requirement.properties

        # Check for business-related keywords in comments or descriptions
        business_keywords = [
            "user", "business", "requirement", "feature", "functionality",
            "purpose", "intent", "goal", "objective", "value"
        ]

        code_business_context = 0
        for prop_value in code_props.values():
            if isinstance(prop_value, str):
                prop_lower = prop_value.lower()
                for keyword in business_keywords:
                    if keyword in prop_lower:
                        code_business_context += 1

        requirement_business_context = 0
        for prop_value in requirement_props.values():
            if isinstance(prop_value, str):
                prop_lower = prop_value.lower()
                for keyword in business_keywords:
                    if keyword in prop_lower:
                        requirement_business_context += 1

        # Normalize scores
        code_score = min(1.0, code_business_context / 5)  # Max 5 business keywords
        requirement_score = min(1.0, requirement_business_context / 3)  # Max 3 business keywords

        return (code_score + requirement_score) / 2

    def _analyze_implementation_patterns(self, code_entity: Entity, requirement: Entity) -> float:
        """Analyze implementation patterns for intent alignment."""
        # Check if implementation matches requirement type
        code_type = code_entity.type
        requirement_desc = requirement.properties.get("description", "").lower()

        # Pattern matching based on requirement type and implementation
        if "validate" in requirement_desc or "test" in requirement_desc:
            if code_type in ["Function", "Class"]:  # Could be validation logic
                return 0.8

        if "store" in requirement_desc or "persist" in requirement_desc:
            if code_type in ["Class"]:  # Could be data model or repository
                return 0.7

        if "display" in requirement_desc or "show" in requirement_desc:
            if code_type in ["Function"]:  # Could be UI logic
                return 0.6

        return 0.3  # Default low confidence

    def _determine_intent_type(self, code_entity: Entity, requirement: Entity, confidence: float) -> str:
        """Determine the type of intent relationship."""
        requirement_desc = requirement.properties.get("description", "").lower()

        # High confidence suggests direct implementation
        if confidence > 0.8:
            if "validate" in requirement_desc or "test" in requirement_desc:
                return "VALIDATES"
            else:
                return "IMPLEMENTS"

        # Medium confidence suggests satisfaction of requirement
        elif confidence > 0.6:
            return "SATISFIES"

        # Lower confidence suggests related functionality
        else:
            return "RELATED_TO"
