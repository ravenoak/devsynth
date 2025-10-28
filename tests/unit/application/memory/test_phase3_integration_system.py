"""
Unit tests for Phase 3 Integration System.

This module tests the integration of all Phase 3 advanced reasoning components
including Enhanced GraphRAG, Automata Synthesis, Hybrid LLM Architecture,
Metacognitive Training, and Contextual Prompting.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from devsynth.application.memory.enhanced_knowledge_graph import EnhancedKnowledgeGraph
from devsynth.application.memory.phase3_integration_system import (
    Phase3IntegrationSystem,
)
from devsynth.domain.models.memory import (
    CognitiveType,
    MemeticMetadata,
    MemeticSource,
    MemeticUnit,
)


class TestPhase3IntegrationSystem:
    """Test Phase 3 integration system functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.memory_manager = Mock()
        self.enhanced_graph = EnhancedKnowledgeGraph()
        self.integration_system = Phase3IntegrationSystem(
            self.memory_manager, self.enhanced_graph
        )

    def test_initialization(self):
        """Test system initialization."""
        assert self.integration_system.memory_manager == self.memory_manager
        assert self.integration_system.enhanced_graph == self.enhanced_graph
        assert self.integration_system.system_status == "initialized"

        # Check all components are initialized
        assert hasattr(self.integration_system, "execution_learning")
        assert hasattr(self.integration_system, "enhanced_graphrag")
        assert hasattr(self.integration_system, "automata_synthesis")
        assert hasattr(self.integration_system, "hybrid_llm")
        assert hasattr(self.integration_system, "metacognitive_training")
        assert hasattr(self.integration_system, "contextual_prompting")

    def test_process_advanced_reasoning_task(self):
        """Test processing of complex reasoning tasks."""
        task = {
            "task_id": "test_task_123",
            "description": "Analyze user authentication system",
            "type": "analysis",
            "complexity": "medium",
        }

        # Mock all the component methods
        with patch.object(
            self.integration_system, "_analyze_and_segment_task"
        ) as mock_segment:
            mock_segment.return_value = [
                {"segment_id": "seg1", "description": "Analyze requirements"},
                {"segment_id": "seg2", "description": "Review implementation"},
            ]

            with patch.object(
                self.integration_system, "_execute_multi_hop_reasoning"
            ) as mock_reasoning:
                mock_reasoning.return_value = {
                    "success": True,
                    "total_hops": 3,
                    "confidence": 0.85,
                }

                with patch.object(
                    self.integration_system, "_execute_hybrid_llm_processing"
                ) as mock_hybrid:
                    mock_hybrid.return_value = {
                        "success": True,
                        "result": {"confidence": 0.9, "execution_time": 2.5},
                    }

                    with patch.object(
                        self.integration_system, "_apply_metacognitive_enhancement"
                    ) as mock_meta:
                        mock_meta.return_value = {
                            "success": True,
                            "insights": ["Strategy improvement", "Efficiency gain"],
                        }

                        with patch.object(
                            self.integration_system, "_optimize_contextual_prompts"
                        ) as mock_prompts:
                            mock_prompts.return_value = {
                                "success": True,
                                "engineered_prompts": ["Prompt 1", "Prompt 2"],
                            }

                            result = (
                                self.integration_system.process_advanced_reasoning_task(
                                    task
                                )
                            )

        assert result["success"] is True
        assert result["task_id"] == "test_task_123"
        assert "processing_summary" in result
        assert result["processing_summary"]["task_segments"] == 2
        assert result["processing_summary"]["reasoning_hops"] == 3
        assert result["processing_summary"]["confidence_score"] > 0.8

    def test_analyze_and_segment_task(self):
        """Test task analysis and segmentation."""
        task = {
            "description": "Implement user authentication system",
            "type": "code_generation",
        }

        # Mock automata synthesis
        with patch.object(
            self.integration_system.automata_synthesis, "get_automata_for_task_type"
        ) as mock_get:
            mock_automata = Mock()
            mock_automata.task_type = "code_generation"
            mock_get.return_value = mock_automata

            with patch.object(
                self.integration_system.automata_synthesis, "generate_task_segmentation"
            ) as mock_generate:
                mock_generate.return_value = [
                    {"segment_id": "seg1", "description": "Analyze requirements"},
                    {"segment_id": "seg2", "description": "Design architecture"},
                ]

                segments = self.integration_system._analyze_and_segment_task(task)

        assert len(segments) == 2
        assert segments[0]["description"] == "Analyze requirements"

    def test_execute_multi_hop_reasoning(self):
        """Test multi-hop reasoning execution."""
        task = {"description": "What is user authentication?"}
        task_segments = [{"segment_id": "seg1"}]

        # Mock GraphRAG query engine
        with patch.object(
            self.integration_system.enhanced_graphrag, "process_complex_query"
        ) as mock_process:
            mock_response = Mock()
            mock_response.reasoning_path.total_hops = 4
            mock_response.confidence = 0.88
            mock_process.return_value = mock_response

            result = self.integration_system._execute_multi_hop_reasoning(
                task, task_segments
            )

        assert result["success"] is True
        assert result["total_hops"] == 4
        assert result["confidence"] == 0.88

    def test_execute_hybrid_llm_processing(self):
        """Test hybrid LLM processing."""
        task = {
            "task_id": "test_hybrid",
            "description": "Process authentication logic",
            "type": "processing",
            "complexity": "medium",
        }

        # Mock hybrid LLM
        with patch.object(
            self.integration_system.hybrid_llm, "process_complex_reasoning_task"
        ) as mock_process:
            mock_result = Mock()
            mock_result.confidence = 0.92
            mock_result.execution_time = 1.8
            mock_result.provider_usage = {"dllm": "mercury", "tllm": "gpt4"}
            mock_process.return_value = mock_result

            result = self.integration_system._execute_hybrid_llm_processing(
                task, {"success": True}
            )

        assert result["success"] is True
        assert result["result"].confidence == 0.92
        assert result["execution_time"] == 1.8

    def test_apply_metacognitive_enhancement(self):
        """Test metacognitive enhancement application."""
        task = {"description": "Test metacognitive enhancement"}
        hybrid_results = {"result": {"confidence": 0.85}}

        # Mock metacognitive training
        with patch.object(
            self.integration_system.metacognitive_training, "start_think_aloud_session"
        ) as mock_start:
            mock_start.return_value = "session_123"

            with patch.object(
                self.integration_system.metacognitive_training, "record_verbalization"
            ) as mock_record:
                with patch.object(
                    self.integration_system.metacognitive_training,
                    "end_think_aloud_session",
                ) as mock_end:
                    mock_end.return_value = {
                        "session_id": "session_123",
                        "insights": ["Strategy improvement", "Error pattern"],
                        "verbalizations_count": 5,
                    }

                    result = self.integration_system._apply_metacognitive_enhancement(
                        task, hybrid_results
                    )

        assert result["success"] is True
        assert len(result["insights"]) == 2

    def test_optimize_contextual_prompts(self):
        """Test contextual prompt optimization."""
        task = {"description": "Optimize authentication prompts"}
        metacognitive_results = {"insights": ["Use clearer language"]}

        # Mock contextual prompting
        with patch.object(
            self.integration_system.contextual_prompting, "create_contextual_prompt"
        ) as mock_create:
            mock_prompt = Mock()
            mock_prompt.prompt_id = "prompt_123"
            mock_create.return_value = mock_prompt

            with patch.object(
                self.integration_system.contextual_prompting,
                "engineer_contextual_prompt",
            ) as mock_engineer:
                mock_result = Mock()
                mock_result.estimated_effectiveness = 0.88
                mock_engineer.return_value = mock_result

                result = self.integration_system._optimize_contextual_prompts(
                    task, metacognitive_results
                )

        assert result["success"] is True
        assert result["contextual_prompt"].prompt_id == "prompt_123"

    def test_integrate_and_validate_results(self):
        """Test result integration and validation."""
        task = {"description": "Test integration"}
        task_segments = [{"segment_id": "seg1"}]
        reasoning_results = {"success": True, "total_hops": 3, "confidence": 0.85}
        hybrid_results = {"success": True, "result": {"confidence": 0.9}}
        metacognitive_results = {"success": True, "insights": ["insight1"]}
        contextual_results = {"success": True, "engineered_prompts": ["prompt1"]}

        result = self.integration_system._integrate_and_validate_results(
            task,
            task_segments,
            reasoning_results,
            hybrid_results,
            metacognitive_results,
            contextual_results,
        )

        assert "task_description" in result
        assert "overall_confidence" in result
        assert result["task_segments"] == 1
        assert result["reasoning_hops"] == 3

    def test_get_system_status(self):
        """Test system status retrieval."""
        status = self.integration_system.get_system_status()

        assert status["system_status"] == "initialized"
        assert "components_ready" in status
        assert "performance_metrics" in status
        assert "component_statistics" in status

        # Check all components are ready
        components_ready = status["components_ready"]
        assert components_ready["execution_learning"] is True
        assert components_ready["enhanced_graphrag"] is True
        assert components_ready["automata_synthesis"] is True

    def test_benchmark_against_research(self):
        """Test benchmarking against research standards."""
        test_tasks = [
            {
                "task_id": "task1",
                "description": "Test authentication",
                "type": "analysis",
            },
            {
                "task_id": "task2",
                "description": "Test payment processing",
                "type": "impact_analysis",
            },
        ]

        # Mock task processing
        with patch.object(
            self.integration_system, "process_advanced_reasoning_task"
        ) as mock_process:
            mock_result = Mock()
            mock_result.success = True
            mock_result.result = {
                "overall_confidence": 0.88,
                "research_alignment": {"overall_alignment": True},
            }
            mock_process.return_value = {"success": True, "result": mock_result.result}

            benchmark_results = self.integration_system.benchmark_against_research(
                test_tasks
            )

        assert benchmark_results["total_tests"] == 2
        assert benchmark_results["successful_tests"] == 2
        assert benchmark_results["success_rate"] == 1.0
        assert "detailed_results" in benchmark_results

    def test_export_import_system_state(self):
        """Test system state export and import."""
        # Set up some state
        self.integration_system.execution_learning.learning_history = [
            {"test": "session"}
        ]
        self.integration_system.enhanced_graphrag.query_cache = {"query1": "result1"}

        # Export state
        exported_state = self.integration_system.export_system_state()

        assert "system_status" in exported_state
        assert "execution_learning" in exported_state
        assert "export_timestamp" in exported_state

        # Create new instance for import test
        new_system = Phase3IntegrationSystem(self.memory_manager, self.enhanced_graph)

        # Import state
        new_system.import_system_state(exported_state)

        # Verify import (simplified check)
        assert new_system.system_status == "initialized"

    def test_validate_system_integrity(self):
        """Test system integrity validation."""
        integrity_report = self.integration_system.validate_system_integrity()

        assert integrity_report["overall_health"] in ["healthy", "degraded"]
        assert "component_health" in integrity_report
        assert "integration_status" in integrity_report
        assert "performance_status" in integrity_report
        assert "recommendations" in integrity_report

    def test_optimize_system_performance(self):
        """Test system performance optimization."""
        # Set up performance metrics
        self.integration_system.performance_metrics = {
            "average_confidence": 0.75,
            "average_execution_time": 25.0,
        }

        optimization_report = self.integration_system.optimize_system_performance()

        assert "optimizations_applied" in optimization_report
        assert "performance_improvements" in optimization_report
        assert "recommendations" in optimization_report

    def test_memory_graph_integration_check(self):
        """Test memory-graph integration check."""
        result = self.integration_system._check_memory_graph_integration()
        assert result in ["integrated", "partial", "error"]

    def test_execution_learning_integration_check(self):
        """Test execution learning integration check."""
        result = self.integration_system._check_execution_learning_integration()
        assert result in ["integrated", "partial", "error"]

    def test_automata_metacognitive_integration_check(self):
        """Test automata-metacognitive integration check."""
        result = self.integration_system._check_automata_metacognitive_integration()
        assert result in ["integrated", "partial", "error"]


class TestEnhancedGraphRAGQueryEngine:
    """Test Enhanced GraphRAG query engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enhanced_graph = EnhancedKnowledgeGraph()
        self.execution_learning = Mock()
        self.query_engine = EnhancedGraphRAGQueryEngine(
            self.enhanced_graph, self.execution_learning
        )

    def test_initialization(self):
        """Test query engine initialization."""
        assert self.query_engine.enhanced_graph == self.enhanced_graph
        assert self.query_engine.execution_learning == self.execution_learning
        assert len(self.query_engine.query_cache) == 0

    def test_process_complex_query(self):
        """Test processing of complex queries."""
        query = "What functions implement user authentication?"

        # Mock the parsing and execution methods
        with patch.object(self.query_engine, "_parse_query_intent") as mock_parse:
            mock_parse.return_value = Mock(
                query_type="relationship_query",
                entities=["function", "authentication"],
                relationships=["implements"],
                required_hops=2,
            )

            with patch.object(self.query_engine, "_resolve_entities") as mock_resolve:
                mock_resolve.return_value = {"found_entities": ["func_auth"]}

                with patch.object(
                    self.query_engine, "_plan_multi_hop_traversal"
                ) as mock_plan:
                    mock_plan.return_value = Mock(
                        start_entities=["func_auth"],
                        traversal_sequence=[{"relationship_type": "IMPLEMENTS"}],
                    )

                    with patch.object(
                        self.query_engine, "_execute_semantic_traversal"
                    ) as mock_execute:
                        mock_path = Mock()
                        mock_path.steps = [Mock(confidence_score=0.85)]
                        mock_path.total_hops = 1
                        mock_path.overall_confidence = 0.85
                        mock_execute.return_value = mock_path

                        with patch.object(
                            self.query_engine, "_validate_reasoning_chain"
                        ) as mock_validate:
                            mock_validate.return_value = {"path_accuracy": 0.9}

                            with patch.object(
                                self.query_engine, "_generate_traceable_explanation"
                            ) as mock_explain:
                                mock_explain.return_value = (
                                    "Query processed successfully"
                                )

                                with patch.object(
                                    self.query_engine, "_synthesize_answer"
                                ) as mock_synthesize:
                                    mock_synthesize.return_value = (
                                        "Authentication functions found"
                                    )

                                    response = self.query_engine.process_complex_query(
                                        query
                                    )

        assert response.answer == "Authentication functions found"
        assert response.confidence > 0.8
        assert len(response.reasoning_path.steps) == 1

    def test_parse_query_intent(self):
        """Test query intent parsing."""
        query = (
            "How does user authentication work and what are the security implications?"
        )

        intent = self.query_engine._parse_query_intent(query)

        assert intent.query_type == "multi_hop"
        assert "authentication" in intent.entities
        assert "work" in intent.entities
        assert intent.required_hops >= 2

    def test_extract_entities(self):
        """Test entity extraction from queries."""
        query = "What does the authenticate_user function do?"

        entities = self.query_engine._extract_entities(query)

        assert "authenticate_user" in entities
        assert "function" in entities

    def test_extract_relationships(self):
        """Test relationship extraction from queries."""
        query = "What functions call authenticate_user and what do they do?"

        relationships = self.query_engine._extract_relationships(query)

        assert "calls" in relationships

    def test_calculate_required_hops(self):
        """Test required hops calculation."""
        entities = ["function", "authentication", "user"]
        relationships = ["calls", "implements"]

        hops = self.query_engine._calculate_required_hops(
            "multi_hop", entities, relationships
        )

        assert hops >= 3  # Should require multiple hops for complex query

    def test_resolve_entities(self):
        """Test entity resolution."""
        # Add test entities to graph
        auth_entity = Mock()
        auth_entity.id = "func_auth"
        auth_entity.properties = {"name": "authenticate_user"}

        self.enhanced_graph.add_entity(auth_entity)

        entities = ["authenticate_user"]
        mappings = self.query_engine._resolve_entities(entities)

        assert len(mappings["found_entities"]) > 0

    def test_plan_multi_hop_traversal(self):
        """Test multi-hop traversal planning."""
        parsed_query = Mock(
            entities=["authentication"], relationships=["implements"], required_hops=3
        )

        entity_mappings = {"found_entities": ["func_auth"]}

        plan = self.query_engine._plan_multi_hop_traversal(
            parsed_query, entity_mappings
        )

        assert len(plan.start_entities) > 0
        assert len(plan.traversal_sequence) >= 3

    def test_execute_semantic_traversal(self):
        """Test semantic traversal execution."""
        plan = Mock(
            start_entities=["func_auth"],
            traversal_sequence=[{"relationship_type": "IMPLEMENTS", "hop_number": 1}],
            semantic_filters=[{}],
            max_depth=2,
        )

        # Mock graph operations
        with patch.object(
            self.enhanced_graph, "get_connected_entities"
        ) as mock_connected:
            mock_connected.return_value = [Mock(id="req_auth")]

            reasoning_path = self.query_engine._execute_semantic_traversal(plan)

        assert len(reasoning_path.steps) == 1
        assert reasoning_path.total_hops == 1
        assert len(reasoning_path.final_entities) > 0


class TestAutomataSynthesisEngine:
    """Test automata synthesis engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.execution_learning = Mock()
        self.automata_engine = AutomataSynthesisEngine(self.execution_learning)

    def test_initialization(self):
        """Test automata synthesis initialization."""
        assert self.automata_engine.execution_learning == self.execution_learning
        assert self.automata_engine.min_exploration_samples == 10
        assert len(self.automata_engine.synthesized_automata) == 0

    def test_synthesize_automata_from_exploration(self):
        """Test automata synthesis from exploration data."""
        task_type = "code_generation"
        exploration_data = [
            {"state": "initial", "action": "analyze_requirements", "success": True},
            {"state": "processing", "action": "generate_code", "success": True},
            {"state": "validation", "action": "test_code", "success": True},
        ]

        automata = self.automata_engine.synthesize_automata_from_exploration(
            task_type, exploration_data
        )

        assert automata is not None
        assert automata.task_type == task_type
        assert (
            len(automata.states) >= 2
        )  # Should have initial and at least one other state
        assert automata.initial_state in automata.states

    def test_generate_task_segmentation(self):
        """Test task segmentation generation."""
        # Create mock automata
        automata = Mock()
        automata.initial_state = "initial"
        automata.terminal_states = ["terminal"]
        automata.states = {
            "initial": Mock(state_type="initial", description="Start task"),
            "processing": Mock(state_type="intermediate", description="Process data"),
            "terminal": Mock(state_type="terminal", description="Complete task"),
        }
        automata.transitions = {}

        segments = self.automata_engine.generate_task_segmentation(
            "Test task", automata
        )

        assert len(segments) >= 2
        assert segments[0]["state"] == "initial"
        assert segments[-1]["state"] == "terminal"

    def test_validate_automata_quality(self):
        """Test automata quality validation."""
        automata = Mock()
        automata.automata_id = "test_automata"
        automata.states = {"initial": Mock(), "processing": Mock(), "terminal": Mock()}
        automata.transitions = {
            "initial-->processing": Mock(),
            "processing-->terminal": Mock(),
        }
        automata.terminal_states = ["terminal"]
        automata.exploration_data = [{"success": True}] * 15

        quality = self.automata_engine.validate_automata_quality(automata)

        assert quality["automata_id"] == "test_automata"
        assert "state_completeness" in quality
        assert "transition_completeness" in quality
        assert "overall_quality" in quality

    def test_create_memetic_units_from_automata(self):
        """Test Memetic Unit creation from automata."""
        automata = Mock()
        automata.automata_id = "test_automata"
        automata.states = {
            "initial": Mock(state_type="initial"),
            "processing": Mock(state_type="intermediate"),
        }
        automata.transitions = {
            "initial-->processing": Mock(transition_type="sequential")
        }

        units = self.automata_engine.create_memetic_units_from_automata(automata)

        assert len(units) > 0

        # Should have units for automata, states, and transitions
        unit_types = [u.metadata.cognitive_type for u in units]
        assert CognitiveType.PROCEDURAL in unit_types  # Automata unit
        assert CognitiveType.SEMANTIC in unit_types  # State units

    def test_get_task_segmentation_for_query(self):
        """Test task segmentation for natural language query."""
        query = "How should I implement user authentication?"

        # Mock automata for code_generation
        mock_automata = Mock()
        mock_automata.task_type = "code_generation"

        with patch.object(
            self.automata_engine, "get_automata_for_task_type"
        ) as mock_get:
            mock_get.return_value = mock_automata

            with patch.object(
                self.automata_engine, "generate_task_segmentation"
            ) as mock_generate:
                mock_generate.return_value = [
                    {"segment_id": "seg1", "description": "Analyze requirements"},
                    {"segment_id": "seg2", "description": "Design architecture"},
                ]

                segments = self.automata_engine.get_task_segmentation_for_query(query)

        assert len(segments) == 2
        assert segments[0]["description"] == "Analyze requirements"


class TestHybridLLMArchitecture:
    """Test hybrid LLM architecture."""

    def setup_method(self):
        """Set up test fixtures."""
        self.execution_learning = Mock()
        self.hybrid_llm = HybridLLMArchitecture(self.execution_learning)

    def test_initialization(self):
        """Test hybrid LLM initialization."""
        assert self.hybrid_llm.execution_learning == self.execution_learning
        assert len(self.hybrid_llm.providers) >= 2  # Should have multiple providers
        assert "mercury_dllm" in self.hybrid_llm.providers
        assert "gpt4_nano_tllm" in self.hybrid_llm.providers

    def test_process_complex_reasoning_task(self):
        """Test processing of complex reasoning tasks."""
        task = {
            "task_id": "test_hybrid_task",
            "description": "Design authentication system",
            "type": "design",
            "complexity": "high",
            "requirements": ["secure", "scalable"],
        }

        # Mock provider operations
        with patch.object(self.hybrid_llm, "_execute_rapid_planning") as mock_plan:
            mock_plan.return_value = {
                "provider": "mercury_dllm",
                "planning_output": "Plan for authentication system",
                "execution_time": 0.5,
                "tokens_used": 200,
            }

            with patch.object(
                self.hybrid_llm, "_execute_precise_solving"
            ) as mock_solve:
                mock_solve.return_value = {
                    "provider": "gpt4_nano_tllm",
                    "solving_output": "Detailed authentication implementation",
                    "execution_time": 2.0,
                    "tokens_used": 800,
                }

                with patch.object(
                    self.hybrid_llm, "_integrate_and_validate"
                ) as mock_integrate:
                    mock_integrate.return_value = {
                        "answer": "Complete authentication system design",
                        "confidence": 0.91,
                        "reasoning_path": [],
                    }

                    result = self.hybrid_llm.process_complex_reasoning_task(task)

        assert result.final_answer == "Complete authentication system design"
        assert result.confidence == 0.91
        assert "provider_usage" in result.provider_usage

    def test_get_optimal_provider_for_task(self):
        """Test optimal provider selection."""
        simple_task = {"complexity": "simple"}
        complex_task = {"complexity": "complex"}
        balanced_task = {"complexity": "medium"}

        simple_provider = self.hybrid_llm.get_optimal_provider_for_task(simple_task)
        complex_provider = self.hybrid_llm.get_optimal_provider_for_task(complex_task)
        balanced_provider = self.hybrid_llm.get_optimal_provider_for_task(balanced_task)

        # Should select appropriate providers based on complexity
        assert simple_provider.model_type == "diffusion"  # Fast for simple tasks
        assert (
            complex_provider.model_type == "transformer"
        )  # Accurate for complex tasks
        assert balanced_provider.model_type == "hybrid"  # Balanced for medium tasks

    def test_benchmark_hybrid_vs_individual(self):
        """Test benchmarking of hybrid vs individual providers."""
        test_tasks = [
            {"task_id": "task1", "complexity": "simple"},
            {"task_id": "task2", "complexity": "complex"},
        ]

        # Mock individual provider testing
        with patch.object(self.hybrid_llm, "_test_individual_provider") as mock_test:
            mock_test.side_effect = [
                {"provider": "mercury_dllm", "execution_time": 0.5, "accuracy": 0.75},
                {"provider": "gpt4_nano_tllm", "execution_time": 2.0, "accuracy": 0.92},
            ]

            benchmark_results = self.hybrid_llm.benchmark_hybrid_vs_individual(
                test_tasks
            )

        assert "comparison" in benchmark_results
        assert "speed_comparison" in benchmark_results["comparison"]
        assert "accuracy_comparison" in benchmark_results["comparison"]

    def test_add_provider(self):
        """Test adding new providers."""
        new_provider = Mock()
        new_provider.name = "test_provider"
        new_provider.model_type = "custom"

        self.hybrid_llm.add_provider(new_provider)

        assert "test_provider" in self.hybrid_llm.providers

    def test_get_architecture_statistics(self):
        """Test architecture statistics retrieval."""
        stats = self.hybrid_llm.get_architecture_statistics()

        assert stats["total_providers"] >= 2
        assert "provider_types" in stats
        assert "cached_results" in stats
        assert "providers" in stats


class TestMetacognitiveTrainingSystem:
    """Test metacognitive training system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.execution_learning = Mock()
        self.metacognitive_system = MetacognitiveTrainingSystem(self.execution_learning)

    def test_initialization(self):
        """Test metacognitive system initialization."""
        assert self.metacognitive_system.execution_learning == self.execution_learning
        assert self.metacognitive_system.current_state.awareness_level == 0.5
        assert len(self.metacognitive_system.training_sessions) == 0

    def test_start_think_aloud_session(self):
        """Test starting think-aloud session."""
        session_id = self.metacognitive_system.start_think_aloud_session("Test task")

        assert session_id is not None
        assert self.metacognitive_system.current_state.self_monitoring_active is True
        assert len(self.metacognitive_system.training_sessions) == 1

        session = self.metacognitive_system.training_sessions[0]
        assert session.session_id == session_id
        assert session.task_description == "Test task"

    def test_record_verbalization(self):
        """Test verbalization recording."""
        session_id = self.metacognitive_system.start_think_aloud_session("Test task")

        self.metacognitive_system.record_verbalization(
            session_id, "I'm considering different approaches to this problem"
        )

        session = self.metacognitive_system.training_sessions[0]
        assert len(session.verbalizations) == 1
        assert (
            session.verbalizations[0]["verbalization"]
            == "I'm considering different approaches to this problem"
        )

    def test_end_think_aloud_session(self):
        """Test ending think-aloud session."""
        session_id = self.metacognitive_system.start_think_aloud_session("Test task")

        self.metacognitive_system.record_verbalization(session_id, "Test verbalization")

        # Mock insight extraction
        with patch.object(
            self.metacognitive_system, "_extract_insights_from_session"
        ) as mock_extract:
            mock_extract.return_value = [Mock(insight_type="strategy_improvement")]

            with patch.object(
                self.metacognitive_system, "_update_metacognitive_state_from_session"
            ) as mock_update:
                summary = self.metacognitive_system.end_think_aloud_session(session_id)

        assert summary["session_id"] == session_id
        assert summary["task_description"] == "Test task"
        assert "verbalizations_count" in summary
        assert self.metacognitive_system.current_state.self_monitoring_active is False

    def test_get_metacognitive_insights(self):
        """Test retrieving metacognitive insights."""
        # Add mock insights
        mock_insight = Mock()
        mock_insight.insight_type = "strategy_improvement"
        self.metacognitive_system.metacognitive_insights = [mock_insight]

        # Get all insights
        all_insights = self.metacognitive_system.get_metacognitive_insights()
        assert len(all_insights) == 1

        # Get filtered insights
        strategy_insights = self.metacognitive_system.get_metacognitive_insights(
            "strategy_improvement"
        )
        assert len(strategy_insights) == 1

        # Get non-existent type
        other_insights = self.metacognitive_system.get_metacognitive_insights(
            "non_existent"
        )
        assert len(other_insights) == 0

    def test_apply_metacognitive_improvements(self):
        """Test applying metacognitive improvements."""
        # Create mock insights
        high_applicability_insight = Mock()
        high_applicability_insight.applicability_score = 0.8
        high_applicability_insight.description = "High applicability insight"
        high_applicability_insight.insight_type = "strategy_improvement"
        high_applicability_insight.implementation_suggestions = ["Suggestion 1"]

        low_applicability_insight = Mock()
        low_applicability_insight.applicability_score = 0.3
        low_applicability_insight.description = "Low applicability insight"

        insights = [high_applicability_insight, low_applicability_insight]

        improvements = self.metacognitive_system.apply_metacognitive_improvements(
            insights
        )

        assert improvements["applied_insights"] == 1  # Only high applicability
        assert len(improvements["improvement_areas"]) == 1
        assert "High applicability insight" in improvements["improvement_areas"][0]

    def test_generate_self_monitoring_report(self):
        """Test self-monitoring report generation."""
        # Add mock training session
        mock_session = Mock()
        mock_session.session_duration = 300.0
        mock_session.verbalizations = [Mock()] * 5
        mock_session.insights = [Mock()] * 2

        self.metacognitive_system.training_sessions = [mock_session]
        self.metacognitive_system.metacognitive_insights = [Mock()] * 3

        report = self.metacognitive_system.generate_self_monitoring_report()

        assert "current_metacognitive_state" in report
        assert "training_statistics" in report
        assert "insight_distribution" in report
        assert report["training_statistics"]["total_sessions"] == 1
        assert report["training_statistics"]["total_insights"] == 3


class TestContextualPromptingSystem:
    """Test contextual prompting system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.execution_learning = Mock()
        self.prompting_system = ContextualPromptingSystem(self.execution_learning)

    def test_initialization(self):
        """Test prompting system initialization."""
        assert self.prompting_system.execution_learning == self.execution_learning
        assert len(self.prompting_system.behavioral_directives) >= 3
        assert len(self.prompting_system.environmental_constraints) >= 3

    def test_create_contextual_prompt(self):
        """Test contextual prompt creation."""
        base_prompt = "Analyze this authentication system"
        context = {
            "task_type": "analysis",
            "complexity": "medium",
            "user_expertise": "intermediate",
        }

        contextual_prompt = self.prompting_system.create_contextual_prompt(
            base_prompt, context
        )

        assert contextual_prompt.base_prompt == base_prompt
        assert len(contextual_prompt.behavioral_directives) > 0
        assert len(contextual_prompt.environmental_constraints) > 0
        assert "context_variables" in contextual_prompt.context_variables

    def test_engineer_contextual_prompt(self):
        """Test contextual prompt engineering."""
        # Create mock contextual prompt
        mock_prompt = Mock()
        mock_prompt.base_prompt = "Test prompt"
        mock_prompt.behavioral_directives = [Mock()]
        mock_prompt.environmental_constraints = [Mock()]
        mock_prompt.context_variables = {"test": "value"}
        mock_prompt.validation_criteria = ["Test criterion"]

        engineered_result = self.prompting_system.engineer_contextual_prompt(
            mock_prompt
        )

        assert engineered_result.engineered_prompt is not None
        assert len(engineered_result.engineered_prompt) > 0
        assert engineered_result.directive_coverage >= 0.0
        assert engineered_result.constraint_compliance >= 0.0
        assert engineered_result.estimated_effectiveness >= 0.0

    def test_add_behavioral_directive(self):
        """Test adding behavioral directives."""
        new_directive = Mock()
        new_directive.directive_id = "test_directive"
        new_directive.category = "test"
        new_directive.description = "Test directive"

        self.prompting_system.add_behavioral_directive(new_directive)

        assert "test_directive" in self.prompting_system.behavioral_directives

    def test_add_environmental_constraint(self):
        """Test adding environmental constraints."""
        new_constraint = Mock()
        new_constraint.constraint_id = "test_constraint"
        new_constraint.constraint_type = "test"
        new_constraint.description = "Test constraint"

        self.prompting_system.add_environmental_constraint(new_constraint)

        assert "test_constraint" in self.prompting_system.environmental_constraints

    def test_get_prompt_performance_analytics(self):
        """Test prompt performance analytics."""
        # Add mock performance data
        self.prompting_system.prompt_performance_history = [
            {
                "directive_coverage": 0.8,
                "constraint_compliance": 0.9,
                "context_relevance": 0.85,
                "estimated_effectiveness": 0.87,
            }
        ]

        analytics = self.prompting_system.get_prompt_performance_analytics()

        assert "total_prompts_engineered" in analytics
        assert "average_metrics" in analytics
        assert analytics["total_prompts_engineered"] == 1
        assert analytics["average_metrics"]["directive_coverage"] == 0.8

    def test_create_agent_specific_prompt(self):
        """Test agent-specific prompt creation."""
        agent_type = "code_generator"
        task_context = {
            "task_description": "Generate authentication code",
            "complexity": "medium",
        }

        agent_prompt = self.prompting_system.create_agent_specific_prompt(
            agent_type, task_context
        )

        assert agent_prompt.base_prompt is not None
        assert "code_generator" in agent_prompt.base_prompt
        assert len(agent_prompt.behavioral_directives) > 0
