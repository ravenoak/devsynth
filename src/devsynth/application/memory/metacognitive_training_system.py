"""
Metacognitive Training System for Self-Monitoring

This module implements metacognitive training protocols that enable DevSynth
to monitor, evaluate, and control its cognitive processes through think-aloud
exercises and real-time awareness.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .execution_learning_integration import ExecutionLearningIntegration
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class MetacognitiveState:
    """Represents the current metacognitive state."""
    awareness_level: float  # 0-1 scale
    self_monitoring_active: bool
    strategy_evaluation: Dict[str, float]
    cognitive_load: float
    confidence_calibration: float
    last_reflection: Optional[str] = None
    improvement_areas: List[str] = field(default_factory=list)


@dataclass
class ThinkAloudSession:
    """Represents a think-aloud training session."""
    session_id: str
    task_description: str
    verbalizations: List[Dict[str, Any]] = field(default_factory=list)
    strategy_insights: Dict[str, Any] = field(default_factory=dict)
    cognitive_patterns: Dict[str, Any] = field(default_factory=dict)
    session_start: float = field(default_factory=time.time)
    session_duration: float = 0.0


@dataclass
class MetacognitiveInsight:
    """Represents an insight gained from metacognitive training."""
    insight_id: str
    insight_type: str  # "strategy_improvement", "error_pattern", "efficiency_gain"
    description: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    applicability_score: float = 0.0
    implementation_suggestions: List[str] = field(default_factory=list)


class MetacognitiveTrainingSystem:
    """System for metacognitive training and self-monitoring."""

    def __init__(self, execution_learning: ExecutionLearningIntegration):
        """Initialize the metacognitive training system."""
        self.execution_learning = execution_learning
        self.current_state = MetacognitiveState(
            awareness_level=0.5,
            self_monitoring_active=False,
            strategy_evaluation={},
            cognitive_load=0.0,
            confidence_calibration=0.5
        )

        self.training_sessions: List[ThinkAloudSession] = []
        self.metacognitive_insights: List[MetacognitiveInsight] = []
        self.cognitive_patterns: Dict[str, Dict[str, Any]] = defaultdict(dict)

        logger.info("Metacognitive training system initialized")

    def start_think_aloud_session(self, task_description: str) -> str:
        """Start a think-aloud training session."""
        session_id = f"session_{int(time.time())}_{len(self.training_sessions)}"

        session = ThinkAloudSession(
            session_id=session_id,
            task_description=task_description,
            session_start=time.time()
        )

        self.training_sessions.append(session)
        self.current_state.self_monitoring_active = True

        logger.info(f"Started think-aloud session {session_id} for task: {task_description}")
        return session_id

    def record_verbalization(self, session_id: str, verbalization: str, context: Dict[str, Any] = None) -> None:
        """Record a verbalization during think-aloud training."""
        context = context or {}

        # Find the session
        session = next((s for s in self.training_sessions if s.session_id == session_id), None)

        if not session:
            logger.warning(f"Session {session_id} not found for verbalization")
            return

        # Record verbalization
        verbalization_record = {
            "timestamp": time.time(),
            "verbalization": verbalization,
            "context": context,
            "cognitive_state": self._capture_current_cognitive_state()
        }

        session.verbalizations.append(verbalization_record)

        # Analyze for insights
        self._analyze_verbalization_for_insights(verbalization, context)

        logger.debug(f"Recorded verbalization in session {session_id}")

    def end_think_aloud_session(self, session_id: str) -> Dict[str, Any]:
        """End a think-aloud training session and extract insights."""
        session = next((s for s in self.training_sessions if s.session_id == session_id), None)

        if not session:
            return {"error": f"Session {session_id} not found"}

        # Calculate session duration
        session.session_duration = time.time() - session.session_start

        # Extract insights from the session
        insights = self._extract_insights_from_session(session)

        # Update metacognitive state
        self._update_metacognitive_state_from_session(session, insights)

        # Generate session summary
        summary = {
            "session_id": session_id,
            "task_description": session.task_description,
            "duration": session.session_duration,
            "verbalizations_count": len(session.verbalizations),
            "insights_extracted": len(insights),
            "strategy_improvements": [i.description for i in insights if i.insight_type == "strategy_improvement"],
            "cognitive_patterns": session.cognitive_patterns,
            "session_end": time.time()
        }

        self.current_state.self_monitoring_active = False

        logger.info(f"Ended think-aloud session {session_id} with {len(insights)} insights")
        return summary

    def _analyze_verbalization_for_insights(self, verbalization: str, context: Dict[str, Any]) -> None:
        """Analyze verbalization for potential insights."""
        # Strategy-related verbalizations
        strategy_indicators = [
            "I'm considering", "I should", "Maybe I can", "Another approach",
            "This strategy", "Better way", "More efficient", "Alternative"
        ]

        # Error pattern indicators
        error_indicators = [
            "I made a mistake", "Wrong approach", "Didn't work", "Failed",
            "Error occurred", "Unexpected result", "Bug in"
        ]

        # Efficiency indicators
        efficiency_indicators = [
            "This is taking too long", "Inefficient", "Better method",
            "Time-consuming", "Optimized", "Faster way"
        ]

        verbalization_lower = verbalization.lower()

        # Check for strategy insights
        if any(indicator.lower() in verbalization_lower for indicator in strategy_indicators):
            insight = MetacognitiveInsight(
                insight_id=f"strategy_{int(time.time())}_{len(self.metacognitive_insights)}",
                insight_type="strategy_improvement",
                description=f"Strategy consideration in verbalization: {verbalization[:100]}...",
                confidence=0.7,
                evidence=[verbalization],
                applicability_score=0.6
            )
            self.metacognitive_insights.append(insight)

        # Check for error patterns
        elif any(indicator.lower() in verbalization_lower for indicator in error_indicators):
            insight = MetacognitiveInsight(
                insight_id=f"error_{int(time.time())}_{len(self.metacognitive_insights)}",
                insight_type="error_pattern",
                description=f"Error pattern identified: {verbalization[:100]}...",
                confidence=0.8,
                evidence=[verbalization],
                applicability_score=0.7
            )
            self.metacognitive_insights.append(insight)

        # Check for efficiency gains
        elif any(indicator.lower() in verbalization_lower for indicator in efficiency_indicators):
            insight = MetacognitiveInsight(
                insight_id=f"efficiency_{int(time.time())}_{len(self.metacognitive_insights)}",
                insight_type="efficiency_gain",
                description=f"Efficiency opportunity identified: {verbalization[:100]}...",
                confidence=0.6,
                evidence=[verbalization],
                applicability_score=0.8
            )
            self.metacognitive_insights.append(insight)

    def _extract_insights_from_session(self, session: ThinkAloudSession) -> List[MetacognitiveInsight]:
        """Extract insights from a completed session."""
        insights = []

        # Analyze verbalization patterns
        if session.verbalizations:
            # Strategy analysis
            strategy_count = sum(1 for v in session.verbalizations if "strategy" in str(v).lower())
            if strategy_count > 0:
                strategy_insight = MetacognitiveInsight(
                    insight_id=f"strategy_analysis_{session.session_id}",
                    insight_type="strategy_improvement",
                    description=f"Session showed {strategy_count} strategy considerations",
                    confidence=0.7,
                    evidence=[f"{strategy_count} strategy verbalizations"],
                    applicability_score=0.6
                )
                insights.append(strategy_insight)

            # Cognitive load analysis
            avg_complexity = self._analyze_cognitive_complexity(session)
            if avg_complexity > 0.7:
                complexity_insight = MetacognitiveInsight(
                    insight_id=f"complexity_{session.session_id}",
                    insight_type="cognitive_load",
                    description=f"High cognitive complexity detected (score: {avg_complexity:.2f})",
                    confidence=0.8,
                    evidence=[f"Average complexity: {avg_complexity:.2f}"],
                    applicability_score=0.7
                )
                insights.append(complexity_insight)

        # Extract from session metadata
        session.insights = insights

        return insights

    def _analyze_cognitive_complexity(self, session: ThinkAloudSession) -> float:
        """Analyze cognitive complexity from session verbalizations."""
        if not session.verbalizations:
            return 0.0

        complexity_indicators = [
            "complex", "difficult", "challenging", "multiple", "several",
            "different", "various", "complicated", "intricate"
        ]

        complexity_scores = []

        for verbalization in session.verbalizations:
            text = verbalization.get("verbalization", "").lower()
            indicator_count = sum(1 for indicator in complexity_indicators if indicator in text)
            complexity_scores.append(min(1.0, indicator_count / 3))  # Normalize to 0-1

        return sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0

    def _update_metacognitive_state_from_session(self, session: ThinkAloudSession, insights: List[MetacognitiveInsight]) -> None:
        """Update metacognitive state based on session results."""
        # Update awareness level based on insights
        if insights:
            self.current_state.awareness_level = min(1.0, self.current_state.awareness_level + 0.1)

        # Update strategy evaluation
        strategy_insights = [i for i in insights if i.insight_type == "strategy_improvement"]
        if strategy_insights:
            strategy_avg_confidence = sum(i.confidence for i in strategy_insights) / len(strategy_insights)
            self.current_state.strategy_evaluation["strategy_awareness"] = strategy_avg_confidence

        # Update cognitive load based on session complexity
        complexity_score = self._analyze_cognitive_complexity(session)
        self.current_state.cognitive_load = complexity_score

        # Update confidence calibration
        if session.verbalizations:
            confidence_scores = [v.get("cognitive_state", {}).get("confidence", 0.5) for v in session.verbalizations]
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                self.current_state.confidence_calibration = avg_confidence

        # Record reflection
        self.current_state.last_reflection = f"Session {session.session_id} completed with {len(insights)} insights"

    def _capture_current_cognitive_state(self) -> Dict[str, Any]:
        """Capture current cognitive state for verbalization."""
        return {
            "awareness_level": self.current_state.awareness_level,
            "cognitive_load": self.current_state.cognitive_load,
            "confidence": self.current_state.confidence_calibration,
            "strategy_evaluation": self.current_state.strategy_evaluation,
            "timestamp": time.time()
        }

    def get_metacognitive_insights(self, insight_type: Optional[str] = None) -> List[MetacognitiveInsight]:
        """Get metacognitive insights, optionally filtered by type."""
        if insight_type:
            return [i for i in self.metacognitive_insights if i.insight_type == insight_type]

        return self.metacognitive_insights

    def apply_metacognitive_improvements(self, insights: List[MetacognitiveInsight]) -> Dict[str, Any]:
        """Apply metacognitive improvements based on insights."""
        improvements = {
            "applied_insights": 0,
            "improvement_areas": [],
            "implementation_suggestions": []
        }

        for insight in insights:
            if insight.applicability_score > 0.7:  # High applicability threshold
                # Apply the insight
                self._apply_insight_improvement(insight)
                improvements["applied_insights"] += 1
                improvements["improvement_areas"].append(insight.description)
                improvements["implementation_suggestions"].extend(insight.implementation_suggestions)

        logger.info(f"Applied {improvements['applied_insights']} metacognitive improvements")
        return improvements

    def _apply_insight_improvement(self, insight: MetacognitiveInsight) -> None:
        """Apply a specific metacognitive insight improvement."""
        if insight.insight_type == "strategy_improvement":
            # Update strategy evaluation
            self.current_state.strategy_evaluation[insight.description[:50]] = insight.confidence

        elif insight.insight_type == "error_pattern":
            # Add error pattern to cognitive patterns for future avoidance
            self.cognitive_patterns["error_avoidance"][insight.description] = {
                "confidence": insight.confidence,
                "applicability": insight.applicability_score
            }

        elif insight.insight_type == "efficiency_gain":
            # Update efficiency tracking
            self.cognitive_patterns["efficiency"][insight.description] = {
                "confidence": insight.confidence,
                "improvement_potential": insight.applicability_score
            }

    def generate_self_monitoring_report(self) -> Dict[str, Any]:
        """Generate a comprehensive self-monitoring report."""
        # Calculate session statistics
        total_sessions = len(self.training_sessions)
        total_insights = len(self.metacognitive_insights)

        if total_sessions == 0:
            return {"error": "No training sessions completed"}

        # Calculate average session metrics
        avg_duration = sum(s.session_duration for s in self.training_sessions) / total_sessions
        avg_verbalizations = sum(len(s.verbalizations) for s in self.training_sessions) / total_sessions
        avg_insights = total_insights / total_sessions

        # Analyze insight distribution
        insight_types = defaultdict(int)
        for insight in self.metacognitive_insights:
            insight_types[insight.insight_type] += 1

        # Calculate improvement trends
        improvement_trends = self._calculate_improvement_trends()

        report = {
            "current_metacognitive_state": {
                "awareness_level": self.current_state.awareness_level,
                "self_monitoring_active": self.current_state.self_monitoring_active,
                "cognitive_load": self.current_state.cognitive_load,
                "confidence_calibration": self.current_state.confidence_calibration,
                "strategy_evaluation": self.current_state.strategy_evaluation
            },
            "training_statistics": {
                "total_sessions": total_sessions,
                "total_insights": total_insights,
                "average_duration": avg_duration,
                "average_verbalizations": avg_verbalizations,
                "average_insights_per_session": avg_insights
            },
            "insight_distribution": dict(insight_types),
            "improvement_trends": improvement_trends,
            "cognitive_patterns": dict(self.cognitive_patterns),
            "recommendations": self._generate_self_improvement_recommendations()
        }

        return report

    def _calculate_improvement_trends(self) -> Dict[str, Any]:
        """Calculate improvement trends over time."""
        if len(self.metacognitive_insights) < 2:
            return {"insufficient_data": True}

        # Group insights by time periods
        recent_insights = self.metacognitive_insights[-10:]  # Last 10 insights
        older_insights = self.metacognitive_insights[:-10] if len(self.metacognitive_insights) > 10 else []

        trends = {}

        if older_insights and recent_insights:
            # Compare confidence trends
            older_confidence = sum(i.confidence for i in older_insights) / len(older_insights)
            recent_confidence = sum(i.confidence for i in recent_insights) / len(recent_insights)

            trends["confidence_trend"] = recent_confidence - older_confidence

            # Compare applicability trends
            older_applicability = sum(i.applicability_score for i in older_insights) / len(older_insights)
            recent_applicability = sum(i.applicability_score for i in recent_insights) / len(recent_insights)

            trends["applicability_trend"] = recent_applicability - older_applicability

        return trends

    def _generate_self_improvement_recommendations(self) -> List[str]:
        """Generate recommendations for self-improvement."""
        recommendations = []

        # Check awareness level
        if self.current_state.awareness_level < 0.6:
            recommendations.append("Increase metacognitive awareness through more frequent think-aloud sessions")

        # Check cognitive load
        if self.current_state.cognitive_load > 0.8:
            recommendations.append("Reduce cognitive load through task decomposition and strategy optimization")

        # Check strategy evaluation
        if not self.current_state.strategy_evaluation:
            recommendations.append("Develop strategy evaluation framework through targeted training")

        # Check for specific improvement areas
        improvement_areas = self.current_state.improvement_areas
        if improvement_areas:
            recommendations.append(f"Focus on improving: {', '.join(improvement_areas[:3])}")

        return recommendations

    def export_metacognitive_state(self) -> Dict[str, Any]:
        """Export current metacognitive state for persistence."""
        return {
            "current_state": {
                "awareness_level": self.current_state.awareness_level,
                "self_monitoring_active": self.current_state.self_monitoring_active,
                "strategy_evaluation": self.current_state.strategy_evaluation,
                "cognitive_load": self.current_state.cognitive_load,
                "confidence_calibration": self.current_state.confidence_calibration,
                "last_reflection": self.current_state.last_reflection,
                "improvement_areas": self.current_state.improvement_areas
            },
            "training_sessions": [
                {
                    "session_id": s.session_id,
                    "task_description": s.task_description,
                    "verbalizations_count": len(s.verbalizations),
                    "session_duration": s.session_duration,
                    "insights_count": len(s.insights)
                }
                for s in self.training_sessions
            ],
            "metacognitive_insights": [
                {
                    "insight_id": i.insight_id,
                    "insight_type": i.insight_type,
                    "description": i.description,
                    "confidence": i.confidence,
                    "applicability_score": i.applicability_score
                }
                for i in self.metacognitive_insights
            ],
            "cognitive_patterns": dict(self.cognitive_patterns),
            "export_timestamp": time.time()
        }

    def import_metacognitive_state(self, state_data: Dict[str, Any]) -> None:
        """Import metacognitive state from external source."""
        # Restore current state
        state_info = state_data.get("current_state", {})
        self.current_state.awareness_level = state_info.get("awareness_level", 0.5)
        self.current_state.self_monitoring_active = state_info.get("self_monitoring_active", False)
        self.current_state.strategy_evaluation = state_info.get("strategy_evaluation", {})
        self.current_state.cognitive_load = state_info.get("cognitive_load", 0.0)
        self.current_state.confidence_calibration = state_info.get("confidence_calibration", 0.5)
        self.current_state.last_reflection = state_info.get("last_reflection")
        self.current_state.improvement_areas = state_info.get("improvement_areas", [])

        # Restore training sessions (simplified)
        sessions_info = state_data.get("training_sessions", [])
        self.training_sessions = [
            ThinkAloudSession(
                session_id=s["session_id"],
                task_description=s["task_description"],
                session_duration=s.get("session_duration", 0.0)
            )
            for s in sessions_info
        ]

        # Restore insights (simplified)
        insights_info = state_data.get("metacognitive_insights", [])
        self.metacognitive_insights = [
            MetacognitiveInsight(
                insight_id=i["insight_id"],
                insight_type=i["insight_type"],
                description=i["description"],
                confidence=i["confidence"],
                applicability_score=i.get("applicability_score", 0.0)
            )
            for i in insights_info
        ]

        # Restore cognitive patterns
        self.cognitive_patterns = defaultdict(dict, state_data.get("cognitive_patterns", {}))

        logger.info(f"Imported metacognitive state: {len(self.training_sessions)} sessions, {len(self.metacognitive_insights)} insights")

    def simulate_think_aloud_exercise(self, task_description: str, duration_minutes: int = 5) -> Dict[str, Any]:
        """Simulate a think-aloud exercise for training."""
        session_id = self.start_think_aloud_session(task_description)

        # Simulate verbalizations over time
        verbalization_templates = [
            "I'm considering the approach to this task",
            "I need to break this down into smaller steps",
            "This strategy seems efficient",
            "I should validate my assumptions",
            "This approach might have some limitations",
            "Let me reconsider the requirements",
            "I think I've found a better method",
            "This is taking longer than expected",
            "I need to optimize my thinking process",
            "The solution is becoming clearer now"
        ]

        import random
        verbalization_count = max(3, int(duration_minutes * 2))  # 2 per minute minimum

        for i in range(verbalization_count):
            # Simulate time passing
            time.sleep(0.1)

            # Select random verbalization
            verbalization = random.choice(verbalization_templates)

            # Add some variation
            if i % 3 == 0:
                verbalization = f"I'm thinking: {verbalization}"

            self.record_verbalization(session_id, verbalization, {"simulated": True, "step": i})

        # End session and return results
        return self.end_think_aloud_session(session_id)
