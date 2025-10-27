"""
Enhanced GraphRAG Engine for Multi-Hop Reasoning

This module implements advanced GraphRAG capabilities with multi-hop reasoning,
building on the enhanced knowledge graph and execution learning system to
provide sophisticated query processing and reasoning capabilities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from .enhanced_knowledge_graph import EnhancedKnowledgeGraph, Entity, IntentLink
from .execution_learning_integration import ExecutionLearningIntegration
from ...domain.models.memory import MemeticUnit, MemeticMetadata, MemeticSource, CognitiveType
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class QueryIntent:
    """Represents parsed intent from natural language query."""
    query_type: str  # "entity_info", "relationship_query", "multi_hop", "impact_analysis"
    entities: List[str]
    relationships: List[str]
    required_hops: int
    semantic_constraints: Dict[str, Any]
    reasoning_objective: str


@dataclass
class TraversalPlan:
    """Plan for graph traversal in multi-hop queries."""
    start_entities: List[str]
    traversal_sequence: List[Dict[str, Any]]
    semantic_filters: List[Dict[str, Any]]
    max_depth: int
    pruning_strategy: str


@dataclass
class ReasoningStep:
    """Single step in multi-hop reasoning path."""
    hop_number: int
    from_entities: List[str]
    relationship_traversed: str
    to_entities: List[str]
    semantic_validation: Dict[str, Any]
    confidence_score: float


@dataclass
class ReasoningPath:
    """Complete reasoning path through knowledge graph."""
    steps: List[ReasoningStep]
    final_entities: List[str]
    total_hops: int
    overall_confidence: float


@dataclass
class MultiHopResponse:
    """Response from multi-hop reasoning query."""
    answer: str
    confidence: float
    reasoning_path: ReasoningPath
    explanation: str
    source_entities: List[str]
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)


class EnhancedGraphRAGQueryEngine:
    """Enhanced GraphRAG engine with multi-hop reasoning capabilities."""

    def __init__(self, enhanced_graph: EnhancedKnowledgeGraph, execution_learning: ExecutionLearningIntegration):
        """Initialize the enhanced GraphRAG query engine."""
        self.enhanced_graph = enhanced_graph
        self.execution_learning = execution_learning
        self.query_cache: Dict[str, MultiHopResponse] = {}

        logger.info("Enhanced GraphRAG query engine initialized")

    def process_complex_query(self, natural_language_query: str) -> MultiHopResponse:
        """Process a complex natural language query using enhanced GraphRAG."""
        # Check cache first
        query_hash = self._compute_query_hash(natural_language_query)
        if query_hash in self.query_cache:
            logger.debug(f"Returning cached response for query: {natural_language_query[:50]}...")
            return self.query_cache[query_hash]

        # Parse query for intent and entities
        parsed_query = self._parse_query_intent(natural_language_query)

        # Resolve entities in the knowledge graph
        entity_mappings = self._resolve_entities(parsed_query.entities)

        # Plan graph traversal strategy
        traversal_plan = self._plan_multi_hop_traversal(parsed_query, entity_mappings)

        # Execute graph traversal
        reasoning_path = self._execute_semantic_traversal(traversal_plan)

        # Validate reasoning chain
        validation_results = self._validate_reasoning_chain(reasoning_path)

        # Generate explanation with traceability
        explanation = self._generate_traceable_explanation(reasoning_path, validation_results)

        # Synthesize final answer
        answer = self._synthesize_answer(reasoning_path, parsed_query)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(validation_results, reasoning_path)

        response = MultiHopResponse(
            answer=answer,
            confidence=overall_confidence,
            reasoning_path=reasoning_path,
            explanation=explanation,
            source_entities=self._extract_source_entities(reasoning_path)
        )

        # Cache the response
        self.query_cache[query_hash] = response

        logger.info(f"Processed complex query with {len(reasoning_path.steps)} hops, confidence: {overall_confidence:.2f}")
        return response

    def _parse_query_intent(self, query: str) -> QueryIntent:
        """Parse natural language query to understand required reasoning steps."""
        query_lower = query.lower()

        # Identify query type
        query_type = self._classify_query_type(query_lower)

        # Extract key entities and concepts
        entities = self._extract_entities(query_lower)

        # Extract relationship requirements
        relationships = self._extract_relationships(query_lower)

        # Determine required traversal depth
        required_hops = self._calculate_required_hops(query_type, entities, relationships)

        # Identify semantic constraints
        semantic_constraints = self._extract_semantic_constraints(query_lower)

        # Determine reasoning objective
        reasoning_objective = self._determine_reasoning_objective(query_lower)

        return QueryIntent(
            query_type=query_type,
            entities=entities,
            relationships=relationships,
            required_hops=required_hops,
            semantic_constraints=semantic_constraints,
            reasoning_objective=reasoning_objective
        )

    def _classify_query_type(self, query: str) -> str:
        """Classify query type based on content analysis."""
        # Entity information queries
        if any(keyword in query for keyword in ["what is", "describe", "explain", "tell me about"]):
            return "entity_info"

        # Relationship queries
        elif any(keyword in query for keyword in ["related to", "connected to", "depends on", "calls"]):
            return "relationship_query"

        # Multi-hop queries (complex relationships)
        elif any(keyword in query for keyword in ["how does", "why", "impact", "affect", "chain", "path"]):
            return "multi_hop"

        # Impact analysis queries
        elif any(keyword in query for keyword in ["change", "modify", "update", "blast radius", "impact"]):
            return "impact_analysis"

        # Default to entity info
        return "entity_info"

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entity names from query."""
        # Simple entity extraction based on common patterns
        entities = []

        # Look for quoted strings
        quoted_matches = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted_matches)

        # Look for function/class names (camelCase or snake_case)
        camel_case = re.findall(r'\b([A-Z][a-z]*[A-Z][a-z]*)\b', query)
        snake_case = re.findall(r'\b([a-z]+_[a-z]+)\b', query)

        entities.extend(camel_case)
        entities.extend(snake_case)

        # Look for common technical terms
        technical_terms = [
            "function", "class", "module", "requirement", "test", "user", "authentication",
            "payment", "database", "api", "endpoint", "service", "component"
        ]

        for term in technical_terms:
            if term in query and term not in entities:
                entities.append(term)

        return list(set(entities))  # Remove duplicates

    def _extract_relationships(self, query: str) -> List[str]:
        """Extract relationship types from query."""
        relationships = []

        # Common relationship patterns
        relationship_patterns = {
            "implements": ["implements", "implemented by", "implementation"],
            "calls": ["calls", "called by", "invokes", "uses"],
            "inherits": ["inherits", "extends", "subclass"],
            "depends_on": ["depends on", "requires", "needs"],
            "validates": ["validates", "tests", "verifies"],
            "affects": ["affects", "impacts", "influences"]
        }

        for rel_type, patterns in relationship_patterns.items():
            if any(pattern in query for pattern in patterns):
                relationships.append(rel_type)

        return relationships

    def _calculate_required_hops(self, query_type: str, entities: List[str], relationships: List[str]) -> int:
        """Calculate required traversal depth."""
        base_hops = 1

        # Multi-hop queries typically need more depth
        if query_type == "multi_hop":
            base_hops = 3
        elif query_type == "impact_analysis":
            base_hops = 4

        # More entities typically require more hops
        entity_bonus = min(len(entities), 2)  # Cap at +2
        relationship_bonus = min(len(relationships), 2)  # Cap at +2

        return base_hops + entity_bonus + relationship_bonus

    def _extract_semantic_constraints(self, query: str) -> Dict[str, Any]:
        """Extract semantic constraints from query."""
        constraints = {
            "must_include": [],
            "must_exclude": [],
            "priority": "balanced",
            "confidence_threshold": 0.7
        }

        # Priority indicators
        if any(word in query for word in ["critical", "important", "urgent", "high priority"]):
            constraints["priority"] = "high"
        elif any(word in query for word in ["optional", "nice to have", "low priority"]):
            constraints["priority"] = "low"

        # Inclusion requirements
        if "only" in query or "specifically" in query:
            # Extract specific requirements
            specific_matches = re.findall(r'only\s+([a-zA-Z\s]+)', query)
            constraints["must_include"] = specific_matches

        return constraints

    def _determine_reasoning_objective(self, query: str) -> str:
        """Determine the primary objective of the query."""
        query_lower = query.lower()

        if any(word in query_lower for word in ["explain", "describe", "understand"]):
            return "explanation"
        elif any(word in query_lower for word in ["find", "locate", "identify"]):
            return "discovery"
        elif any(word in query_lower for word in ["impact", "affect", "change"]):
            return "impact_analysis"
        elif any(word in query_lower for word in ["how", "why", "what causes"]):
            return "causal_analysis"
        else:
            return "general_inquiry"

    def _resolve_entities(self, entities: List[str]) -> Dict[str, Any]:
        """Resolve entity names to graph nodes."""
        entity_mappings = {
            "found_entities": [],
            "unresolved_entities": [],
            "fuzzy_matches": [],
            "resolution_confidence": 0.0
        }

        for entity_name in entities:
            # Try exact match first
            exact_match = self._find_entity_by_exact_name(entity_name)
            if exact_match:
                entity_mappings["found_entities"].append(exact_match)
                continue

            # Try fuzzy matching
            fuzzy_matches = self._find_entity_by_fuzzy_name(entity_name)
            if fuzzy_matches:
                entity_mappings["fuzzy_matches"].extend(fuzzy_matches)
            else:
                entity_mappings["unresolved_entities"].append(entity_name)

        # Calculate resolution confidence
        total_entities = len(entities)
        resolved_entities = len(entity_mappings["found_entities"]) + len(entity_mappings["fuzzy_matches"])
        entity_mappings["resolution_confidence"] = resolved_entities / total_entities if total_entities > 0 else 0.0

        return entity_mappings

    def _find_entity_by_exact_name(self, entity_name: str) -> Optional[str]:
        """Find entity by exact name match."""
        # Search through all entities
        for entity in self.enhanced_graph.entities.values():
            # Check entity properties for exact match
            for prop_value in entity.properties.values():
                if isinstance(prop_value, str) and prop_value.lower() == entity_name.lower():
                    return entity.id

        return None

    def _find_entity_by_fuzzy_name(self, entity_name: str) -> List[Dict[str, Any]]:
        """Find entities by fuzzy name matching."""
        matches = []

        entity_lower = entity_name.lower()

        for entity in self.enhanced_graph.entities.values():
            # Check entity properties for partial matches
            for prop_name, prop_value in entity.properties.items():
                if isinstance(prop_value, str):
                    prop_lower = prop_value.lower()

                    # Calculate similarity score
                    if entity_lower in prop_lower or prop_lower in entity_lower:
                        matches.append({
                            "entity_id": entity.id,
                            "matched_property": prop_name,
                            "matched_value": prop_value,
                            "similarity": 0.8  # High similarity for substring matches
                        })

        return matches

    def _plan_multi_hop_traversal(self, parsed_query: QueryIntent, entity_mappings: Dict[str, Any]) -> TraversalPlan:
        """Plan optimal graph traversal strategy."""
        # Start with resolved entities
        start_entities = [entity["entity_id"] for entity in entity_mappings["found_entities"]]
        start_entities.extend([match["entity_id"] for match in entity_mappings["fuzzy_matches"]])

        if not start_entities:
            # If no entities found, start with most relevant entity types
            if "function" in parsed_query.entities:
                start_entities = [eid for eid, entity in self.enhanced_graph.entities.items()
                                if entity.type == "Function"]

        # Plan traversal sequence based on query type
        traversal_sequence = self._plan_relationship_sequence(parsed_query.relationships, parsed_query.required_hops)

        # Add semantic filtering at each hop
        semantic_filters = self._add_semantic_filters(traversal_sequence, parsed_query.semantic_constraints)

        # Optimize for graph structure and performance
        optimized_plan = self._optimize_traversal_plan(traversal_sequence, semantic_filters)

        return TraversalPlan(
            start_entities=start_entities,
            traversal_sequence=optimized_plan,
            semantic_filters=semantic_filters,
            max_depth=parsed_query.required_hops,
            pruning_strategy=self._select_pruning_strategy(parsed_query)
        )

    def _plan_relationship_sequence(self, relationships: List[str], required_hops: int) -> List[Dict[str, Any]]:
        """Plan the sequence of relationships to traverse."""
        sequence = []

        # Map common query patterns to relationship sequences
        relationship_mapping = {
            "implements": ["IMPLEMENTED_BY", "VALIDATES", "DEPENDS_ON"],
            "calls": ["CALLS", "CALLED_BY", "USES"],
            "depends_on": ["DEPENDS_ON", "USES", "REQUIRES"],
            "validates": ["VALIDATES", "TESTS", "VERIFIES"],
            "affects": ["AFFECTS", "IMPACTS", "INFLUENCES"]
        }

        # Build traversal sequence
        hops_completed = 0
        while hops_completed < required_hops and relationships:
            # Select next relationship to traverse
            rel_type = relationships[0] if relationships else "DEPENDS_ON"

            # Get related relationships
            related_rels = relationship_mapping.get(rel_type, [rel_type])

            for rel in related_rels:
                if hops_completed < required_hops:
                    sequence.append({
                        "relationship_type": rel,
                        "hop_number": hops_completed + 1,
                        "direction": "bidirectional"  # Default
                    })
                    hops_completed += 1

            # Remove processed relationship
            if relationships:
                relationships.pop(0)

        # Fill remaining hops with generic traversal
        while hops_completed < required_hops:
            sequence.append({
                "relationship_type": "DEPENDS_ON",
                "hop_number": hops_completed + 1,
                "direction": "outgoing"
            })
            hops_completed += 1

        return sequence

    def _add_semantic_filters(self, traversal_sequence: List[Dict], semantic_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add semantic filtering to traversal steps."""
        filters = []

        for step in traversal_sequence:
            step_filters = {
                "relationship_type": step["relationship_type"],
                "min_confidence": semantic_constraints.get("confidence_threshold", 0.7),
                "must_include": semantic_constraints.get("must_include", []),
                "must_exclude": semantic_constraints.get("must_exclude", []),
                "priority": semantic_constraints.get("priority", "balanced")
            }
            filters.append(step_filters)

        return filters

    def _optimize_traversal_plan(self, traversal_sequence: List[Dict], semantic_filters: List[Dict]) -> List[Dict]:
        """Optimize traversal plan for performance."""
        # Remove redundant steps
        optimized = []
        seen_relationships = set()

        for step in traversal_sequence:
            rel_type = step["relationship_type"]

            # Skip duplicate relationship types in sequence
            if rel_type not in seen_relationships:
                optimized.append(step)
                seen_relationships.add(rel_type)

        return optimized

    def _select_pruning_strategy(self, parsed_query: QueryIntent) -> str:
        """Select pruning strategy based on query characteristics."""
        if parsed_query.query_type == "impact_analysis":
            return "breadth_first"  # For impact analysis, explore all connections
        elif len(parsed_query.entities) > 3:
            return "depth_first"    # For complex queries, prioritize depth
        else:
            return "balanced"       # Default balanced approach

    def _execute_semantic_traversal(self, plan: TraversalPlan) -> ReasoningPath:
        """Execute planned graph traversal with semantic understanding."""
        current_entities = plan.start_entities
        reasoning_steps = []
        visited_entities = set(current_entities)

        for hop_info in plan.traversal_sequence:
            hop_number = hop_info["hop_number"]
            relationship_type = hop_info["relationship_type"]

            # Find connected entities for this relationship
            next_entities = []

            for entity_id in current_entities:
                connected = self.enhanced_graph.get_connected_entities(entity_id, relationship_type)
                next_entities.extend([e.id for e in connected if e.id not in visited_entities])

            # Apply semantic filtering
            filtered_entities = self._apply_semantic_filtering(next_entities, plan.semantic_filters[hop_number - 1])

            # Validate semantic consistency
            validation = self._validate_semantic_consistency(current_entities, filtered_entities, hop_info)

            # Record reasoning step
            reasoning_step = ReasoningStep(
                hop_number=hop_number,
                from_entities=current_entities,
                relationship_traversed=relationship_type,
                to_entities=filtered_entities,
                semantic_validation=validation,
                confidence_score=validation.get("confidence", 0.5)
            )

            reasoning_steps.append(reasoning_step)

            # Update for next hop
            current_entities = filtered_entities
            visited_entities.update(filtered_entities)

            # Stop if no more connections or max depth reached
            if not filtered_entities or hop_number >= plan.max_depth:
                break

        return ReasoningPath(
            steps=reasoning_steps,
            final_entities=current_entities,
            total_hops=len(reasoning_steps),
            overall_confidence=self._calculate_path_confidence(reasoning_steps)
        )

    def _apply_semantic_filtering(self, entity_ids: List[str], filter_config: Dict[str, Any]) -> List[str]:
        """Apply semantic filtering to entity list."""
        filtered = []

        for entity_id in entity_ids:
            entity = self.enhanced_graph.get_entity(entity_id)
            if not entity:
                continue

            # Apply inclusion filters
            must_include = filter_config.get("must_include", [])
            if must_include:
                entity_text = " ".join(str(v) for v in entity.properties.values()).lower()
                if not any(term.lower() in entity_text for term in must_include):
                    continue

            # Apply exclusion filters
            must_exclude = filter_config.get("must_exclude", [])
            if must_exclude:
                entity_text = " ".join(str(v) for v in entity.properties.values()).lower()
                if any(term.lower() in entity_text for term in must_exclude):
                    continue

            # Apply confidence threshold
            min_confidence = filter_config.get("min_confidence", 0.7)
            if self._calculate_entity_confidence(entity) >= min_confidence:
                filtered.append(entity_id)

        return filtered

    def _calculate_entity_confidence(self, entity: Entity) -> float:
        """Calculate confidence score for an entity."""
        # Base confidence on entity properties completeness
        total_props = len(entity.properties)
        non_empty_props = sum(1 for v in entity.properties.values() if v)

        if total_props == 0:
            return 0.0

        completeness_score = non_empty_props / total_props

        # Boost confidence for entities with business context
        business_context_score = 1.0
        if entity.business_context:
            business_context_score = 1.2

        return min(1.0, completeness_score * business_context_score)

    def _validate_semantic_consistency(self, from_entities: List[str], to_entities: List[str], hop_info: Dict) -> Dict[str, Any]:
        """Validate semantic consistency of traversal step."""
        validation = {
            "consistency_score": 0.5,
            "confidence": 0.5,
            "validation_method": "semantic_consistency_check",
            "issues": []
        }

        if not to_entities:
            validation["issues"].append("No connected entities found")
            return validation

        # Check relationship validity
        relationship_type = hop_info["relationship_type"]

        # Validate that the relationship makes semantic sense
        valid_relationships = [
            "IMPLEMENTS", "CALLS", "DEPENDS_ON", "VALIDATES",
            "AFFECTS", "USES", "REQUIRES", "TESTS"
        ]

        if relationship_type not in valid_relationships:
            validation["issues"].append(f"Unknown relationship type: {relationship_type}")

        # Calculate consistency based on entity types and relationships
        from_types = set()
        to_types = set()

        for entity_id in from_entities + to_entities:
            entity = self.enhanced_graph.get_entity(entity_id)
            if entity:
                if entity_id in from_entities:
                    from_types.add(entity.type)
                if entity_id in to_entities:
                    to_types.add(entity.type)

        # Simple consistency check based on entity types
        if "BusinessRequirement" in from_types and "Function" in to_types:
            validation["consistency_score"] = 0.8  # Good semantic consistency
        elif "Function" in from_types and "Function" in to_types:
            validation["consistency_score"] = 0.7  # Reasonable consistency
        else:
            validation["consistency_score"] = 0.5  # Neutral consistency

        validation["confidence"] = validation["consistency_score"]

        return validation

    def _validate_reasoning_chain(self, reasoning_path: ReasoningPath) -> Dict[str, float]:
        """Validate the reasoning chain for accuracy and consistency."""
        validation_results = {
            "path_accuracy": 0.0,
            "consistency_score": 0.0,
            "confidence_calibration": 0.0,
            "overall_validation": 0.0
        }

        if not reasoning_path.steps:
            return validation_results

        # Validate step-by-step consistency
        step_consistencies = []
        step_confidences = []

        for step in reasoning_path.steps:
            step_consistency = step.semantic_validation.get("consistency_score", 0.5)
            step_confidence = step.confidence_score

            step_consistencies.append(step_consistency)
            step_confidences.append(step_confidence)

        # Calculate validation metrics
        validation_results["consistency_score"] = sum(step_consistencies) / len(step_consistencies)
        validation_results["confidence_calibration"] = sum(step_confidences) / len(step_confidences)

        # Path accuracy based on consistency and confidence
        validation_results["path_accuracy"] = (
            validation_results["consistency_score"] * 0.6 +
            validation_results["confidence_calibration"] * 0.4
        )

        validation_results["overall_validation"] = validation_results["path_accuracy"]

        return validation_results

    def _generate_traceable_explanation(self, reasoning_path: ReasoningPath, validation_results: Dict[str, float]) -> str:
        """Generate explanation with traceability information."""
        if not reasoning_path.steps:
            return "No reasoning steps available for explanation."

        explanation_parts = [
            f"Analysis completed with {reasoning_path.total_hops} reasoning steps.",
            f"Overall confidence: {reasoning_path.overall_confidence".2f"}",
            f"Path validation score: {validation_results.get('path_accuracy', 0)".2f"}"
        ]

        # Add step-by-step explanation
        for i, step in enumerate(reasoning_path.steps):
            explanation_parts.append(
                f"Step {i+1}: Traversed {step.relationship_traversed} relationship "
                f"from {len(step.from_entities)} entities to {len(step.to_entities)} entities "
                f"(confidence: {step.confidence_score".2f"})"
            )

        # Add final results
        if reasoning_path.final_entities:
            explanation_parts.append(
                f"Final result: Found {len(reasoning_path.final_entities)} relevant entities"
            )

        return " ".join(explanation_parts)

    def _synthesize_answer(self, reasoning_path: ReasoningPath, parsed_query: QueryIntent) -> str:
        """Synthesize final answer from reasoning path."""
        if not reasoning_path.final_entities:
            return "No relevant information found for the query."

        # Get final entities
        final_entities = [self.enhanced_graph.get_entity(eid) for eid in reasoning_path.final_entities]
        final_entities = [e for e in final_entities if e]

        if not final_entities:
            return "No entities found matching the query criteria."

        # Synthesize answer based on query type and results
        if parsed_query.query_type == "entity_info":
            return self._synthesize_entity_info_answer(final_entities, parsed_query)

        elif parsed_query.query_type == "relationship_query":
            return self._synthesize_relationship_answer(reasoning_path, parsed_query)

        elif parsed_query.query_type == "multi_hop":
            return self._synthesize_multi_hop_answer(reasoning_path, parsed_query)

        elif parsed_query.query_type == "impact_analysis":
            return self._synthesize_impact_analysis_answer(reasoning_path, parsed_query)

        else:
            return self._synthesize_general_answer(final_entities, parsed_query)

    def _synthesize_entity_info_answer(self, entities: List[Entity], parsed_query: QueryIntent) -> str:
        """Synthesize answer for entity information queries."""
        if not entities:
            return "No entities found matching the query."

        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Generate summary
        summary_parts = []

        for entity_type, type_entities in entities_by_type.items():
            count = len(type_entities)
            summary_parts.append(f"Found {count} {entity_type.lower()}(s)")

            # Add details for first few entities
            for entity in type_entities[:3]:
                key_props = {k: v for k, v in entity.properties.items() if v and len(str(v)) < 100}
                if key_props:
                    summary_parts.append(f"  - {entity_type}: {key_props}")

        return ". ".join(summary_parts)

    def _synthesize_relationship_answer(self, reasoning_path: ReasoningPath, parsed_query: QueryIntent) -> str:
        """Synthesize answer for relationship queries."""
        # Analyze the reasoning path to understand relationships
        relationship_summary = []

        for step in reasoning_path.steps:
            rel_type = step.relationship_traversed
            from_count = len(step.from_entities)
            to_count = len(step.to_entities)

            relationship_summary.append(
                f"Found {to_count} entities connected via {rel_type} relationship "
                f"from {from_count} starting entities"
            )

        return ". ".join(relationship_summary)

    def _synthesize_multi_hop_answer(self, reasoning_path: ReasoningPath, parsed_query: QueryIntent) -> str:
        """Synthesize answer for multi-hop queries."""
        if len(reasoning_path.steps) == 0:
            return "No multi-hop relationships found."

        # Describe the path taken
        path_description = []

        for i, step in enumerate(reasoning_path.steps):
            path_description.append(
                f"Step {i+1}: {step.relationship_traversed} → "
                f"{len(step.to_entities)} entities"
            )

        total_path = ". ".join(path_description)

        return f"Multi-hop analysis revealed: {total_path}. Final result: {len(reasoning_path.final_entities)} entities found."

    def _synthesize_impact_analysis_answer(self, reasoning_path: ReasoningPath, parsed_query: QueryIntent) -> str:
        """Synthesize answer for impact analysis queries."""
        # Calculate impact metrics
        total_entities = len(reasoning_path.final_entities)
        total_hops = reasoning_path.total_hops

        impact_summary = f"Impact analysis identified {total_entities} affected entities across {total_hops} relationship layers."

        # Add confidence information
        if reasoning_path.overall_confidence > 0.7:
            impact_summary += " High confidence in impact assessment."
        elif reasoning_path.overall_confidence > 0.5:
            impact_summary += " Moderate confidence in impact assessment."
        else:
            impact_summary += " Low confidence in impact assessment - manual review recommended."

        return impact_summary

    def _synthesize_general_answer(self, entities: List[Entity], parsed_query: QueryIntent) -> str:
        """Synthesize general answer for unclassified queries."""
        if not entities:
            return "No relevant information found."

        entity_summary = f"Found {len(entities)} entities related to the query."

        # Add entity type breakdown
        type_counts = {}
        for entity in entities:
            entity_type = entity.type
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        type_breakdown = ", ".join([f"{count} {entity_type}" for entity_type, count in type_counts.items()])
        entity_summary += f" Breakdown: {type_breakdown}."

        return entity_summary

    def _calculate_overall_confidence(self, validation_results: Dict[str, float], reasoning_path: ReasoningPath) -> float:
        """Calculate overall confidence in the response."""
        # Weight validation results and path confidence
        validation_score = validation_results.get("path_accuracy", 0.5)
        path_confidence = reasoning_path.overall_confidence

        return (validation_score * 0.6 + path_confidence * 0.4)

    def _extract_source_entities(self, reasoning_path: ReasoningPath) -> List[str]:
        """Extract source entities that contributed to the final result."""
        source_entities = set()

        # Collect all entities from the reasoning path
        for step in reasoning_path.steps:
            source_entities.update(step.from_entities)
            source_entities.update(step.to_entities)

        return list(source_entities)

    def _calculate_path_confidence(self, reasoning_steps: List[ReasoningStep]) -> float:
        """Calculate confidence in the reasoning path."""
        if not reasoning_steps:
            return 0.0

        # Average confidence across all steps
        step_confidences = [step.confidence_score for step in reasoning_steps]
        return sum(step_confidences) / len(step_confidences)

    def _compute_query_hash(self, query: str) -> str:
        """Compute hash for query caching."""
        import hashlib
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def clear_cache(self) -> None:
        """Clear the query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_queries": len(self.query_cache),
            "cache_hit_rate": 0.0  # Would need hit/miss tracking for this
        }
